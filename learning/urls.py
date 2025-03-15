from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core Views
    path('', views.dashboard, name='dashboard'),
    path('documents/', views.documents_view, name='documents'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('chat/', views.chat_view, name='chat'),
    
    # Document Processing
    path('process-document/', views.process_document, name='process_document'),
    path('generate-quiz/', views.generate_quiz, name='generate_quiz'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # API Endpoints
    # path('api/chat/', views.handle_chat_interaction, name='chat_api'),
    # path('api/voice/', views.process_voice, name='voice_api'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('api/chat/', views.handle_chat_interaction, name='chat_api'),
    path('process-voice/', views.process_voice, name='process_voice'),

]