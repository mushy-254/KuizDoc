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

        # Process document
        text_content = ''
        if document.content_type == 'application/pdf':
            pdf_reader = PdfReader(document)
            text_content = '\n'.join(
                [page.extract_text() for page in pdf_reader.pages]
            )
        else:
            text_content = document.read().decode()

        # Prepare Gemini API request
        api_key = os.getenv('GEMINI_API_KEY')
        prompt = textwrap.dedent(f"""
        Analyze this document and answer the user's question.
        
        DOCUMENT CONTENT:
        {text_content[:15000]}  # Limit to 15k characters
        
        USER QUESTION: {question}
        
        INSTRUCTIONS:
        1. Provide a comprehensive answer
        2. Include key points from the document
        3. Use markdown formatting for clarity
        4. Keep response under 500 words
        """)

        response = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}',
            json={
                'contents': [{
                    'parts': [{'text': prompt}]
                }]
            },
            timeout=30
        )
        response.raise_for_status()

        # Parse response
        result = response.json()
        ai_response = result['candidates'][0]['content']['parts'][0]['text']
        
        return JsonResponse({'ai_response': ai_response})

    except Exception as e:
        return JsonResponse(
            {'error': f'Error processing request: {str(e)}'},
            status=500
        )