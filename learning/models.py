from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)