from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Built-in Django Admin (bonus)
    path('django-admin/', admin.site.urls),
    
    # Custom Admin Portal matching the original PHP admin
    path('admin-panel/', include('apps.store_admin.urls', namespace='store_admin')),
    
    # Authentication & Accounts
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    
    # Shopping Cart
    path('cart/', include('apps.cart.urls', namespace='cart')),
    
    # Orders & Checkout
    path('orders/', include('apps.orders.urls', namespace='orders')),
    
    # Store front, catalog, recommendations, pages
    path('', include('apps.store.urls', namespace='store')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
