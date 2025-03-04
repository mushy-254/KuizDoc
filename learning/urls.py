from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('process-document/', views.process_document, name='process_document'),
    path('generate-quiz/', views.generate_quiz, name='generate_quiz'),
    path('chat-interaction/', views.handle_chat_interaction, name='chat_interaction'),
    path('process-voice/', views.process_voice, name='process_voice'),
    # path('summarize-voice/', views.handle_voice_summary, name='voice_summary'),
]