import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'admin':
            return redirect('store_admin:dashboard')
        return redirect('store:home')

    if request.session.pop('account_deleted', False):
        messages.error(request, 'Your account has been deleted by an administrator.')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Try to find user by email or username
        user_obj = User.query if hasattr(User, 'query') else None
        user_record = User.objects.filter(email__iexact=email).first()
        username_to_auth = user_record.username if user_record else email

        user = authenticate(request, username=username_to_auth, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name or user.username}!')
            if user.user_type == 'admin':
                return redirect('store_admin:dashboard')
            return redirect('store:home')
        else:
            messages.error(request, 'Incorrect email or password!')

    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        cpassword = request.POST.get('cpassword', '')
        user_type = request.POST.get('user_type', 'user').lower()

        errors = []
        if not re.search(r'[a-zA-Z]', name):
            errors.append('Name must contain letters!')

        if not email.endswith('@gmail.com'):
            errors.append('Email must be a valid @gmail.com address!')

        if User.objects.filter(email__iexact=email).exists():
            errors.append('Email already registered! Please use a different email or login.')

        if user_type == 'admin':
            if User.objects.filter(user_type='admin').exists():
                errors.append('Only one admin can be registered!')
        else:
            user_type = 'user'

        if password != cpassword:
            errors.append('Confirm password does not match!')

        if len(password) < 4:
            errors.append('Password must be at least 4 characters long!')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                name=name,
                user_type=user_type,
                is_staff=(user_type == 'admin'),
                is_superuser=(user_type == 'admin')
            )
            messages.success(request, 'Registered successfully! Please login.')
            return redirect('accounts:login')

    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')

@csrf_exempt
def check_availability(request):
    if request.method == 'POST':
        req_type = request.POST.get('type')
        value = request.POST.get('value', '').strip()

        if not req_type or not value:
            import json
            try:
                body = json.loads(request.body)
                req_type = body.get('type')
                value = body.get('value', '').strip()
            except Exception:
                pass

        if req_type == 'username':
            exists = User.objects.filter(name__iexact=value).exists() or User.objects.filter(username__iexact=value).exists()
            return JsonResponse({'available': not exists})
        elif req_type == 'email':
            exists = User.objects.filter(email__iexact=value).exists()
            return JsonResponse({'available': not exists})

    return JsonResponse({'error': 'Invalid request'}, status=400)
