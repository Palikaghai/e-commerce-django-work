from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import logging
from .forms import SignupPageForm

logger = logging.getLogger(__name__) 


# Helper: send a small welcome email and log failures
def _send_welcome_email(email, name=None):
    subject = "Welcome to Glow & Beauty!"
    text = f"Hi {name or ''},\n\nThanks for joining Glow & Beauty. Use code GLOW10 for 10% off your first order.\n\n— Glow & Beauty Team"
    html = f"<p>Hi {name or ''},</p><p>Thanks for joining Glow & Beauty. Use code <strong>GLOW10</strong> for 10% off your first order.</p><p>— Glow & Beauty Team</p>"
    try:
        # Use fail_silently=False so exceptions bubble and get logged
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [email], html_message=html, fail_silently=False)
    except Exception as exc:
        logger.exception('Failed to send welcome email to %s', email)
        # Do not raise – we don't want to stop signup on mail failures
        return False
    return True


# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user
            login(request, user)  # Logs the user in
            try:
                _send_welcome_email(user.email, user.first_name or user.username)
            except Exception as exc:
                logger.exception('Error sending welcome email after signup for %s', user.email)
            messages.success(request, f"Welcome {user.username}! Your account was created.")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'user_auth/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'user_auth/login.html', {'form': form})


# Keep existing helper for backward compatibility (not used by URLs now)
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log them in immediately after signing up
            try:
                _send_welcome_email(user.email, user.first_name or user.username)
            except Exception as exc:
                logger.exception('Error sending welcome email after signup_view for %s', user.email)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'user_auth/signup.html', {'form': form})


def signup_ajax(request):
    """AJAX endpoint to create user with additional fields: name, email, country, phone, password1, password2."""
    from django.contrib.auth.models import User

    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': ['Invalid request method']}, status=400)

    # Support form-encoded requests too
    data = request.POST
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    country = data.get('country', '').strip()
    phone = data.get('phone', '').strip()
    password1 = data.get('password1', '')
    password2 = data.get('password2', '')

    errors = []
    if not name:
        errors.append('Name is required')
    if not email:
        errors.append('Email is required')
    if password1 != password2 or not password1:
        errors.append('Passwords do not match or are empty')
    if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
        errors.append('A user with this email already exists')

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    try:
        # Create user
        user = User.objects.create_user(username=email, email=email, password=password1)
        # store the full name in first_name (split if possible)
        if ' ' in name:
            first, last = name.split(' ', 1)
            user.first_name = first
            user.last_name = last
        else:
            user.first_name = name
        user.save()

        # Create profile
        from .models import Profile
        Profile.objects.create(user=user, phone=phone, country=country)

        # Send welcome email
        try:
            _send_welcome_email(user.email, user.first_name or name)
        except Exception as exc:
            logger.exception('Error sending welcome email on signup_ajax for %s', user.email)

        # Log in
        login(request, user)

        return JsonResponse({'success': True, 'redirect': '/'})
    except Exception as exc:
        # Return useful error message
        return JsonResponse({'success': False, 'errors': [str(exc) or 'An unknown error occurred']} , status=500)


def signup_page(request):
    """Full-page signup with richer form"""
    if request.method == 'POST':
        form = SignupPageForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                _send_welcome_email(user.email, user.first_name or user.username)
            except Exception as exc:
                logger.exception('Error sending welcome email on signup_page for %s', user.email)
            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('home')
    else:
        form = SignupPageForm()
    return render(request, 'user_auth/signup_page.html', {'form': form})


def signup_ajax(request):
    """AJAX endpoint to create user with additional fields: name, email, country, phone, password1, password2."""
    from django.contrib.auth.models import User
    import json

    if request.method != 'POST':
        return JsonResponse({'success': False, 'errors': ['Invalid request method']}, status=400)

    # Support form-encoded requests too
    data = request.POST
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    country = data.get('country', '').strip()
    phone = data.get('phone', '').strip()
    password1 = data.get('password1', '')
    password2 = data.get('password2', '')

    errors = []
    if not name:
        errors.append('Name is required')
    if not email:
        errors.append('Email is required')
    if password1 != password2 or not password1:
        errors.append('Passwords do not match or are empty')
    if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
        errors.append('A user with this email already exists')

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # Create user
    user = User.objects.create_user(username=email, email=email, password=password1)
    # store the full name in first_name (split if possible)
    if ' ' in name:
        first, last = name.split(' ', 1)
        user.first_name = first
        user.last_name = last
    else:
        user.first_name = name
    user.save()

    # Create profile
    from .models import Profile
    Profile.objects.create(user=user, phone=phone, country=country)

    # Send welcome email
    try:
        _send_welcome_email(user.email, user.first_name or name)
    except Exception:
        pass

    # Log in
    login(request, user)

    return JsonResponse({'success': True, 'redirect': '/'})

