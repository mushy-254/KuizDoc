from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    quiz_credits = models.PositiveIntegerField(default=5)
    average_score = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Document(models.Model):
    user = models.ForeignKey(User, related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    
    def __str__(self):
        return self.file.name

class Quiz(models.Model):
    CATEGORIES = [
        ('PHY', 'Physics'),
        ('MATH', 'Mathematics'),
        ('BIO', 'Biology')
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=4, choices=CATEGORIES)
    difficulty = models.PositiveIntegerField()
    questions = models.ManyToManyField('Question')

class Question(models.Model):
    text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=200)
    explanation = models.TextField()

