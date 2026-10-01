from importlib import import_module
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin


class AdminSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/admin-panel/'):
            engine = import_module(settings.SESSION_ENGINE)
            session_key = request.COOKIES.get('admin_sessionid')
            request.session = engine.SessionStore(session_key)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/admin-panel/'):
            if hasattr(request, 'user') and request.user.is_authenticated:
                if request.user.user_type != 'admin' and not request.user.is_staff and not request.user.is_superuser:
                    request.user = AnonymousUser()

    def process_response(self, request, response):
        if request.path.startswith('/admin-panel/') and hasattr(request, 'session'):
            if request.session.is_empty():
                response.delete_cookie('admin_sessionid', path='/')
            elif request.session.modified:
                request.session.save()
                response.set_cookie(
                    'admin_sessionid',
                    request.session.session_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    path='/',
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    secure=settings.SESSION_COOKIE_SECURE or False,
                    httponly=settings.SESSION_COOKIE_HTTPONLY or False,
                    samesite=settings.SESSION_COOKIE_SAMESITE or 'Lax',
                )
        return response
