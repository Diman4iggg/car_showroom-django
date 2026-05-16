from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, initial='client', label='Роль')

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
