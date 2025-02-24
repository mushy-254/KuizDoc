from django.shortcuts import render
from .models import UserProfile, Quiz

def dashboard(request):
    # profile = UserProfile.objects.get(user=request.user)
    # quizzes = Quiz.objects.filter(category='PHY')[:3]  # Example physics quizzes
    
    # return render(request, 'dashboard.html}')
    return render(request, 'dashboard.html')
