from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    streak = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    premium_member = models.BooleanField(default=False)

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