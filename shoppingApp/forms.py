from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User



class RegistrationForm(UserCreationForm):

    address = forms.CharField(max_length=512)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password1")