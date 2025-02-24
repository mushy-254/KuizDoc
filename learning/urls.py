from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ask-question/', views.ask_question, name='ask_question'),
    path('submit-question/', views.ask_question, name='submit_quiz'),

    # Add other paths for quiz, progress, etc.
]