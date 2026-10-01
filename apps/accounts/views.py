import re
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db.models import Q
from apps.store.recommendations import (
    get_iso_size_recommendation_knn,
    infer_user_size_profile_from_purchases,
    get_hybrid_recommendations,
)
from apps.orders.models import Order
from apps.store.models import Product

User = get_user_model()


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == 'admin' or request.user.is_staff or request.user.is_superuser:
            return redirect('store_admin:dashboard')
        return redirect('store:home')

    if request.session.pop('account_deleted', False):
        messages.error(request, 'Your account has been deleted by an administrator.')

    if request.method == 'POST':
        login_input = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user_record = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input)).first()
        username_to_auth = user_record.username if user_record else login_input

        user = authenticate(request, username=username_to_auth, password=password)
        if user is not None:
            if user.user_type == 'admin' or user.is_staff or user.is_superuser:
                messages.error(request, 'Admin accounts cannot log in through the user login page. Please log in via the Admin Portal.')
                return redirect('store_admin:admin_login')
            login(request, user)
            messages.success(request, f'Welcome back, {user.name or user.username}!')
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and not next_url.startswith('/admin'):
                return redirect(next_url)
            return redirect('store:home')
        else:
            messages.error(request, 'Incorrect email or password!')

    return render(request, 'accounts/login.html')


@ensure_csrf_cookie
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
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            User.objects.create_user(
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


@login_required(login_url='accounts:login')
@ensure_csrf_cookie
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        foot_length_raw = request.POST.get('foot_length', '').strip()
        unit = request.POST.get('unit', 'cm').strip()
        fit_pref = user.fit_preference or 'standard'
        submitted_fit_pref = request.POST.get('fit_preference', '').strip()
        shoe_size_pref = request.POST.get('shoe_size_preference', '').strip()

        if name:
            user.name = name

        if submitted_fit_pref in ['standard', 'snug', 'loose']:
            fit_pref = submitted_fit_pref
            user.fit_preference = fit_pref

        if foot_length_raw:
            try:
                fl_val = float(foot_length_raw)
                res = get_iso_size_recommendation_knn(fl_val, unit=unit, fit_preference=fit_pref)
                if res:
                    user.foot_length_cm = res['foot_length_cm']
                    user.shoe_size_preference = str(res['primary_eu'])
                    messages.success(
                        request,
                        f"Size profile calculated! Recommended size: EU {res['primary_eu']} ({res['confidence_percent']}% confidence)."
                    )
                else:
                    messages.error(request, "Please enter a valid positive foot length measurement.")
            except ValueError:
                messages.error(request, "Invalid foot length number provided.")
        elif shoe_size_pref:
            user.shoe_size_preference = shoe_size_pref
            messages.success(request, f"Saved preferred size: EU {shoe_size_pref}.")

        user.save()
        return redirect('accounts:profile')

    size_recommendation = None
    if user.foot_length_cm:
        size_recommendation = get_iso_size_recommendation_knn(
            user.foot_length_cm,
            unit='cm',
            fit_preference=user.fit_preference or 'standard'
        )

    purchase_profile = infer_user_size_profile_from_purchases(user.id)

    target_size = None
    if size_recommendation:
        target_size = str(size_recommendation['primary_eu'])
    elif user.shoe_size_preference:
        target_size = str(user.shoe_size_preference)
    elif purchase_profile:
        target_size = str(purchase_profile['primary_eu'])

    matching_shoes = []
    if target_size:
        for p in Product.objects.filter(quantity__gt=0):
            parsed_sizes = [s.strip() for s in (p.sizes or '').split(',') if s.strip()]
            if target_size in parsed_sizes:
                matching_shoes.append(p)
                if len(matching_shoes) >= 8:
                    break

    hybrid_recommendations = get_hybrid_recommendations(user_id=user.id, limit=8)

    user_orders = Order.objects.filter(user_id=user.id).order_by('-id')
    orders_count = user_orders.count()
    recent_orders = user_orders[:4]

    context = {
        'profile_user': user,
        'size_recommendation': size_recommendation,
        'purchase_profile': purchase_profile,
        'target_size': target_size,
        'matching_shoes': matching_shoes,
        'hybrid_recommendations': hybrid_recommendations,
        'orders_count': orders_count,
        'recent_orders': recent_orders,
    }
    return render(request, 'accounts/profile.html', context)


@login_required(login_url='accounts:login')
def foot_size_view(request):
    return render(request, 'accounts/foot_size.html', {'profile_user': request.user})

