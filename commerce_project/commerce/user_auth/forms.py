from django import forms
from django.contrib.auth.models import User
from .models import Profile

class SignupPageForm(forms.Form):
    name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    country = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=30, required=False)
    password1 = forms.CharField(widget=forms.PasswordInput(), required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(), required=True)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match')
        return cleaned

    def save(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        country = self.cleaned_data.get('country', '')
        phone = self.cleaned_data.get('phone', '')
        password = self.cleaned_data['password1']

        user = User.objects.create_user(username=email, email=email, password=password)
        if ' ' in name:
            first, last = name.split(' ', 1)
            user.first_name = first
            user.last_name = last
        else:
            user.first_name = name
        user.save()
        Profile.objects.create(user=user, phone=phone, country=country)
        return user