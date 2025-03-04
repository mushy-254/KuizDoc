import openai
import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, Quiz, Question
from PyPDF2 import PdfReader
from docx import Document

def process_document(document):
    """Extract text from different file formats"""
    text = ""
    try:
        if document.content_type == 'application/pdf':
            pdf_reader = PdfReader(document)
            text = '\n'.join([page.extract_text() for page in pdf_reader.pages])
        elif document.content_type == 'text/plain':
            text = document.read().decode()
        elif document.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = Document(document)
            text = '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise Exception(f"Error processing document: {str(e)}")
    return text

def generate_summary(text):
    """Generate summary using OpenAI"""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Generate a comprehensive summary in bullet points with key concepts and important details."},
                {"role": "user", "content": text[:10000]}  # Limit input size
            ],
            temperature=0.3
        )
        return response.choices[0].message['content']
    except Exception as e:
        raise Exception(f"Summary generation failed: {str(e)}")

def generate_quiz(text, user):
    """Generate quiz questions from document content"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Generate 5 quiz questions in JSON format. Each question should have:
                - question: The question text
                - options: 4 possible answers
                - correct_answer: Index of correct option (0-3)
                - explanation: Brief explanation"""},
                {"role": "user", "content": text[:8000]}
            ],
            temperature=0.5
        )
        
        questions_data = json.loads(response.choices[0].message['content'])
        quiz = Quiz.objects.create(
            title=f"Generated Quiz - {user.username}",
            category='GEN',
            difficulty=3,
            user=user
        )
        
        for q in questions_data:
            Question.objects.create(
                quiz=quiz,
                text=q['question'],
                options=q['options'],
                correct_answer=q['correct_answer'],
                explanation=q['explanation']
            )
        
        return quiz
    except Exception as e:
        raise Exception(f"Quiz generation failed: {str(e)}")

@csrf_exempt  # Only for development, use proper CSRF protection in production
@require_POST
def process_voice(request):
    """Handle voice input processing and AI response generation"""
    try:
        # Get audio file from request
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        # Set up OpenAI API
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Step 1: Transcribe audio using Whisper
        with audio_file.open('rb') as audio:
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio
            )
        
        transcribed_text = transcription['text']

        # Step 2: Get context from active document if provided
        document_context = ""
        if 'document' in request.FILES:
            document = request.FILES['document']
            document_context = process_document(document)  # Your existing document processing function

        # Step 3: Generate AI response using ChatGPT
        messages = [
            {"role": "system", "content": """You are an intelligent learning assistant. 
             Provide clear, concise answers and explain complex concepts simply.
             If relevant, include examples or analogies to aid understanding."""},
            {"role": "user", "content": f"""Context: {document_context[:1000] if document_context else ''}
             Question: {transcribed_text}"""}
        ]

        chat_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        ai_response = chat_response.choices[0].message['content']

        # Step 4: Generate audio response using Text-to-Speech
        audio_response = openai.Audio.create(
            model="tts-1",
            voice="alloy",  # You can choose different voices: alloy, echo, fable, onyx, nova, shimmer
            input=ai_response
        )

        # Return both text and audio responses
        return JsonResponse({
            'success': True,
            'transcription': transcribed_text,
            'ai_response': ai_response,
            'audio_url': audio_response.url  # OpenAI provides a temporary URL for the audio
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Error processing voice input: {str(e)}'
        }, status=500)

# Update the existing chat interaction handler to support voice
@require_POST
def handle_chat_interaction(request):
    """Handle both text and voice chat interactions"""
    try:
        # Check if this is a voice or text interaction
        if 'audio' in request.FILES:
            # Process voice input
            return process_voice(request)
        else:
            # Process text input (your existing logic)
            question = request.POST.get('question', '')
            if not question:
                return JsonResponse({'error': 'No question provided'}, status=400)

            # Generate AI response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful learning assistant."},
                    {"role": "user", "content": question}
                ],
                temperature=0.7
            )

            answer_text = response.choices[0].message['content']

            return JsonResponse({
                'success': True,
                'response': answer_text
            })

    except Exception as e:
        return JsonResponse({
            'error': f'Error processing chat interaction: {str(e)}'
        }, status=500)

# Core Dashboard View
def dashboard(request):
    # Add your dashboard logic here
    context = {
        'user': request.user,
        'stats': {
            'documents_processed': 0,
            'quizzes_taken': 0,
            'average_score': 0
        }
    }
    return render(request, 'dashboard.html', context)

# Document Processing View
@require_POST
def process_document(request):
    try:
        document = request.FILES['document']
        # Add document processing logic
        return JsonResponse({'status': 'success', 'summary': 'Sample summary'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Quiz Generation View
@require_POST
def generate_quiz(request):
    try:
        # Add quiz generation logic
        return JsonResponse({'status': 'success', 'quiz_id': 1})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)