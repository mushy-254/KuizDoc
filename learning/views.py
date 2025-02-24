from django.shortcuts import render
from .models import UserProfile, Quiz

def dashboard(request):
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
        'user': request.user
    }
    return render(request, 'dashboard.html', context)