from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access the admin area.')
            return redirect('accounts:login')
        if request.user.user_type != 'admin' and not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, 'Access denied. Administrator privileges required.')
            return redirect('store:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
