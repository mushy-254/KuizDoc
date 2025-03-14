from asyncio.log import logger
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse

# Add to existing imports
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import DocumentUploadForm, CustomUserCreationForm
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

@login_required
# @require_POST
def process_document_view(request):
    """Document processing endpoint with error handling"""
    try:
        if not request.FILES.get('document'):
            return JsonResponse({'error': 'No document provided'}, status=400)
        
        document = request.FILES['document']
        if document.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("File size exceeds 10MB limit")
        
        text = process_document(document)
        summary = generate_summary(text)
        
        return JsonResponse({
            'status': 'success',
            'summary': summary,
            'word_count': len(text.split())
        })
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=413)
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        return JsonResponse({'error': 'Document processing failed'}, status=500)

@login_required
# @require_POST
def generate_quiz_view(request):
    """Quiz generation endpoint with rate limiting"""
    try:
        if request.user.profile.quiz_credits < 1:
            raise PermissionDenied("No quiz credits remaining")
        
        document_id = request.POST.get('document_id')
        document = get_object_or_404(Document, id=document_id, user=request.user)
        quiz = generate_quiz(document.content, request.user)
        
        request.user.profile.quiz_credits -= 1
        request.user.profile.save()
        
        return JsonResponse({
            'status': 'success',
            'quiz_id': quiz.id,
            'credits_remaining': request.user.profile.quiz_credits
        })
    except PermissionDenied as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        logger.error(f"Quiz generation error: {str(e)}")
        return JsonResponse({'error': 'Quiz generation failed'}, status=500)




def analytics_view(request):
    # Dummy data for quick stats
    quick_stats = [
        {
            'title': 'Total Documents',
            'value': '156',
            'icon': 'fas fa-file-alt',
            'bg_color': 'bg-purple-600',
            'trend': '+12%',
            'trend_color': 'text-green-500'
        },
        {
            'title': 'Study Hours',
            'value': '47.5',
            'icon': 'fas fa-clock',
            'bg_color': 'bg-blue-600',
            'trend': '+8%',
            'trend_color': 'text-green-500'
        },
        {
            'title': 'Topics Mastered',
            'value': '12',
            'icon': 'fas fa-brain',
            'bg_color': 'bg-green-600',
            'trend': '+3',
            'trend_color': 'text-green-500'
        },
        {
            'title': 'Achievement Score',
            'value': '892',
            'icon': 'fas fa-trophy',
            'bg_color': 'bg-yellow-600',
            'trend': '+15%',
            'trend_color': 'text-green-500'
        }
    ]

    # Dummy data for recent documents
    recent_documents = [
        {
            'name': 'Machine Learning Basics',
            'date': '2 hours ago',
            'pages': 24,
            'progress': 85,
            'type_color': 'bg-blue-600',
            'icon': 'fas fa-file-pdf'
        },
        {
            'name': 'Data Structures Notes',
            'date': 'Yesterday',
            'pages': 18,
            'progress': 60,
            'type_color': 'bg-green-600',
            'icon': 'fas fa-file-word'
        },
        {
            'name': 'Algorithm Analysis',
            'date': '3 days ago',
            'pages': 32,
            'progress': 95,
            'type_color': 'bg-purple-600',
            'icon': 'fas fa-file-alt'
        }
    ]

    # Dummy data for topic mastery
    topics = [
        {
            'name': 'Machine Learning',
            'progress': 85,
            'last_studied': 'Today',
            'strength': 'Advanced',
            'strength_color': 'bg-green-100 text-green-800',
            'progress_color': 'bg-green-600'
        },
        {
            'name': 'Data Structures',
            'progress': 70,
            'last_studied': 'Yesterday',
            'strength': 'Intermediate',
            'strength_color': 'bg-blue-100 text-blue-800',
            'progress_color': 'bg-blue-600'
        },
        {
            'name': 'Algorithms',
            'progress': 90,
            'last_studied': '2 days ago',
            'strength': 'Advanced',
            'strength_color': 'bg-purple-100 text-purple-800',
            'progress_color': 'bg-purple-600'
        },
        {
            'name': 'Database Systems',
            'progress': 65,
            'last_studied': '3 days ago',
            'strength': 'Intermediate',
            'strength_color': 'bg-yellow-100 text-yellow-800',
            'progress_color': 'bg-yellow-600'
        }
    ]

    # Dummy data for achievements
    recent_achievements = [
        {
            'name': 'Study Marathon',
            'description': 'Completed 8 hours of focused study',
            'date': 'Today',
            'icon': 'fas fa-award',
            'gradient': 'from-purple-600 to-indigo-600'
        },
        {
            'name': 'Perfect Week',
            'description': 'Maintained study streak for 7 days',
            'date': 'Yesterday',
            'icon': 'fas fa-star',
            'gradient': 'from-blue-600 to-cyan-600'
        },
        {
            'name': 'Quick Learner',
            'description': 'Completed 5 documents in one day',
            'date': '2 days ago',
            'icon': 'fas fa-bolt',
            'gradient': 'from-green-600 to-teal-600'
        }
    ]

    # Dummy data for charts
    doc_type_labels = json.dumps(['PDF', 'Word', 'Notes', 'Presentations'])
    doc_type_data = json.dumps([45, 25, 20, 10])
    
    weekly_progress_labels = json.dumps(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
    weekly_progress_data = json.dumps([65, 75, 70, 85, 80, 90, 85])

    # Streak data
    streak_data = {
        'current_streak': 12,
        'longest_streak': 21,
        'total_study_days': 45,
        'avg_daily_progress': 85,
        'streak_days': [
            {'completed': True},
            {'completed': True},
            {'completed': True},
            {'completed': True},
            {'completed': True},
            {'completed': False},
            {'completed': True}
        ]
    }

    context = {
        'quick_stats': quick_stats,
        'recent_documents': recent_documents,
        'topics': topics,
        'recent_achievements': recent_achievements,
        'total_achievements': 24,
        'doc_type_labels': doc_type_labels,
        'doc_type_data': doc_type_data,
        'weekly_progress_labels': weekly_progress_labels,
        'weekly_progress_data': weekly_progress_data,
        **streak_data
    }

    return render(request, 'analytics.html', context)


def chat_view(request):
    return render(request, 'chat.html')


def profile_view(request):
    return render(request, 'profile.html')








@login_required
@require_http_methods(["POST"])
def handle_chat_interaction(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        document_id = data.get('documentId')
        use_voice = data.get('useVoice', False)
        voice_name = data.get('voiceName', 'Sarah')
        
        # Get document context if provided
        document_context = None
        if document_id:
            document = get_object_or_404(Document, id=document_id, user=request.user)
            document_context = document.content
        
        # Get AI text response (use your preferred AI provider)
        ai_response = get_ai_response(message, document_context)
        
        response_data = {
            'textResponse': ai_response,
        }
        
        # Generate voice if requested
        if use_voice:
            audio_url = generate_eleven_labs_audio(ai_response, voice_name)
            response_data['audioUrl'] = audio_url
            response_data['voice'] = voice_name
        
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"Chat interaction error: {str(e)}")
        return JsonResponse({'error': 'Failed to process your request'}, status=500)
    


def generate_eleven_labs_audio(text, voice_name):
    """Generate audio using Eleven Labs API"""
    try:
        import requests
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        
        # Map voice names to IDs (you'd store these in your settings)
        voice_map = {
            'Sarah': 'voice_id_for_sarah',
            'George': 'voice_id_for_george',
            # Add more voices here
        }
        
        voice_id = voice_map.get(voice_name, voice_map['Sarah'])
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.ELEVEN_LABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(
            url.format(voice_id=voice_id),
            json=data,
            headers=headers
        )
        
        if response.status_code == 200:
            # Save the audio file and return the URL
            # In a real implementation, you'd save this to storage
            file_name = f"response_{uuid.uuid4()}.mp3"
            file_path = os.path.join(settings.MEDIA_ROOT, 'audio', file_name)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return settings.MEDIA_URL + f'audio/{file_name}'
        else:
            logger.error(f"Eleven Labs API error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Eleven Labs API error: {str(e)}")
        return None