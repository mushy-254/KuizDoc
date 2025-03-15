import json
import os
import uuid
import requests
import openai
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from core import settings
from .forms import DocumentUploadForm, CustomUserCreationForm
from .models import UserProfile, Quiz, Question, Document, Document

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
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        return render(request, 'registration/register.html', {'form': form})
    
    return render(request, 'registration/register.html', {
        'form': CustomUserCreationForm()
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'registration/login.html', {
            'error': 'Invalid credentials'
        })
    
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    try:
        context = {
            'user': request.user,
            'stats': {
                'documents_processed': request.user.documents.count(),
                'quizzes_taken': 0,  # Update with your quiz model
                'average_score': request.user.profile.average_score
            }
        }
        return render(request, 'dashboard.html', context)
    except Exception as e:
        # logger.error(f"Dashboard error: {str(e)}")
        print(f"Dashboard error: {str(e)}")
        return render(request, 'error.html', status=500)


@login_required
@require_http_methods(["GET", "POST"])
def documents_view(request):
    """Document management view with form handling"""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.user = request.user
                document.save()
                return redirect('documents')
            except Exception as e:
                form.add_error(None, f"Error processing document: {str(e)}")
        return render(request, 'documents.html', {'form': form})
    
    form = DocumentUploadForm()
    return render(request, 'documents.html', {
        'documents': request.user.documents.all(),
        'form': form
    })

@csrf_exempt
@require_POST
def handle_chat(request):
    """Handle both text and voice chat interactions with AI"""
    try:
        data = request.POST if request.POST else json.loads(request.body)
        message = data.get('message', '')
        document_id = data.get('documentId')
        use_voice = data.get('useVoice', False)
        voice_name = data.get('voiceName', 'Sarah')
        
        # Get document context if provided
        document_context = ""
        if document_id:
            try:
                document = Document.objects.get(id=document_id)
                document_context = document.content[:5000]  # Limit context length
            except Document.DoesNotExist:
                pass

        # Get AI text response
        ai_response = get_ai_response(message, document_context)
        
        response_data = {'textResponse': ai_response}
        
        # Generate voice if requested
        if use_voice:
            audio_url = generate_eleven_labs_audio(ai_response, voice_name)
            if audio_url:
                response_data['audioUrl'] = audio_url
        
        return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_ai_response(prompt, context=""):
    """Get response from OpenAI's API"""
    openai.api_key = settings.OPENAI_API_KEY
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": f"You are a helpful tutor. Use this context if relevant: {context}"
            }, {
                "role": "user", 
                "content": prompt
            }],
            temperature=0.7
        )
        return response.choices[0].message['content']
    except Exception as e:
        raise Exception(f"AI request failed: {str(e)}")

def generate_eleven_labs_audio(text, voice_name):
    """Generate audio using Eleven Labs API"""
    try:
        voice_map = settings.ELEVEN_LABS_VOICES
        voice_id = voice_map.get(voice_name, voice_map['Sarah'])
        
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
            json={"text": text[:1000], "model_id": "eleven_multilingual_v2"},
            headers={"xi-api-key": settings.ELEVEN_LABS_API_KEY}
        )
        
        if response.status_code == 200:
            filename = f"audio/{uuid.uuid4()}.mp3"
            full_path = os.path.join(settings.MEDIA_ROOT, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(response.content)
            
            return f"{settings.MEDIA_URL}{filename}"
        return None
        
    except Exception as e:
        raise Exception(f"Audio generation failed: {str(e)}")

# Document Processing View

@csrf_exempt
@require_POST
def process_document(request):
    """Handle document upload and processing"""
    try:
        if 'document' not in request.FILES:
            return JsonResponse({'error': 'No document provided'}, status=400)
        
        document = request.FILES['document']
        text = extract_text(document)
        summary = generate_summary(text)
        
        return JsonResponse({
            'name': document.name,
            'summary': summary,
            'size': document.size
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def extract_text(document):
    """Extract text from uploaded documentxtract text from uploaded document"""
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


def analytics_view(request):
    # Add your analytics logic here
    return render(request, 'analytics.html')

def chat_view(request):
    # Add your chat view logic here
    return render(request, 'chat.html')

def profile_view(request):
    # Add your profile view logic here
    return render(request, 'profile.html')