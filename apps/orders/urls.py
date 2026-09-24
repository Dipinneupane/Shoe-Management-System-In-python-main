from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/khalti-initiate/', views.khalti_initiate, name='khalti_initiate'),
    path('checkout/khalti-return/', views.khalti_return, name='khalti_return'),
    path('history/', views.order_history, name='history'),
    path('api/details/<int:order_id>/', views.order_details_api, name='details_api'),
]
