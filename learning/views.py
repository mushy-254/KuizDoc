from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import UserProfile, Quiz
import requests
from requests.exceptions import ConnectionError
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from PyPDF2 import PdfReader
from io import BytesIO
import textwrap

def dashboard(request):
    error_message = None
    if request.method == 'POST' and request.FILES.get('document'):
        document = request.FILES['document']
        fs = FileSystemStorage()
        filename = fs.save(document.name, document)
        uploaded_file_url = fs.url(filename)

        # Retrieve the API key from environment variables
        api_key = os.getenv('GEMINI_API_KEY')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'multipart/form-data'
        }

        try:
            # Send the file to Gemini AI for summarization
            response = requests.post(
                'https://gemini-ai-api.com/summarize',
                headers=headers,
                files={'file': document}
            )
            response.raise_for_status()  # Raise an error for bad responses
            summary = response.json().get('summary', 'No summary available.')
        except ConnectionError:
            error_message = 'Failed to connect to the summarization service.'
        except requests.HTTPError as e:
            error_message = f'HTTP error occurred: {e}'
        except Exception as e:
            error_message = f'An error occurred: {e}'

        if not error_message:
            print(summary)
            return redirect('dashboard')

    context = {
        'active_section': request.GET.get('section', 'dashboard'),
        'stats': [
            {'value': '92%', 'label': 'Average Score'},
            {'value': '15', 'label': 'Days Streak'},
            {'value': '247', 'label': 'Questions Answered'}
        ],
        'progress_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'progress_data': [65, 78, 82, 75, 90, 85, 88],
        'documents': [
            {'title': 'Quantum Physics Notes', 'last_modified': '2 hours ago'},
            # ... other documents
        ],
        'user': request.user,
        'error_message': error_message
    }
    return render(request, 'dashboard.html', context)

def extract_text(document):
    """Extract text content from uploaded document."""
    if document.content_type == 'application/pdf':
        pdf_reader = PdfReader(document)
        return '\n'.join(
            [page.extract_text() for page in pdf_reader.pages]
        )
    return document.read().decode()

def ask_openai(question, document_text):
    print(f"********* hello i'm being callled")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError('OPENAI_API_KEY environment variable is not set')
        
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"""
    Analyze this document and answer the user's question.
    
    DOCUMENT CONTENT:
    {document_text[:12000]}
    
    USER QUESTION: {question}
    
    Respond in markdown format with clear sections.
    """
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json={
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that analyzes documents and answers questions about them."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )
    print(f"the response was: {response.json()}")
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

@require_POST
def ask_question(request):
    try:
        # Validate input
        question = request.POST.get('question', '').strip()
        document = request.FILES.get('document')
        
        if not question or not document:
            return JsonResponse(
                {'error': 'Both question and document are required'}, 
                status=400
            )

        # Process document and get AI response
        text_content = extract_text(document)
        ai_response = ask_openai(question, text_content)
        
        # Clean the AI response for speech synthesis
        speech_text = ' '.join(ai_response.split('\n')).replace('#', '').replace('*', '')
        
        # Add logging
        print("AI Response:", ai_response)
        
        return JsonResponse({
            'ai_response': ai_response,
            'speech_text': speech_text  # Add clean text for speech
        })

    except ValueError as e:
        print("ValueError:", str(e))
        return JsonResponse({'error': str(e)}, status=500)
    except requests.RequestException as e:
        print("RequestException:", str(e))
        return JsonResponse(
            {'error': f'Error communicating with OpenAI API: {str(e)}'}, 
            status=500
        )
    except Exception as e:
        print("Unexpected error:", str(e))
        return JsonResponse(
            {'error': f'Error processing request: {str(e)}'},
            status=500
        )