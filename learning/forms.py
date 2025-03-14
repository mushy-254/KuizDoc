from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Document

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'accept': '.pdf,.docx,.txt',
                'class': 'hidden'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Limit file size to 10MB
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size exceeds 10MB limit")
            # Validate file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'txt']:
                raise forms.ValidationError("Unsupported file format")
        return file