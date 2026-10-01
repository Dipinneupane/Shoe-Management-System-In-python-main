from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Ensures only administrators can access store_admin views.
    Unauthenticated users and non-admins are directed to admin login.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, 'Please log in with your administrator account.')
            return redirect('store_admin:admin_login')
        if request.user.user_type != 'admin' and not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, 'Access denied. Administrator privileges required.')
            return redirect('store_admin:admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def customer_only(view_func):
    """
    Passthrough decorator ensuring store views remain accessible to all visitors.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view
