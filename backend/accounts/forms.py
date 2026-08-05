from django import forms
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'city', 'photo']


class PasswordChangeForm(DjangoPasswordChangeForm):
    pass
