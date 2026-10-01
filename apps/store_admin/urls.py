from django.urls import path
from . import views

app_name = 'store_admin'

urlpatterns = [
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('', views.dashboard, name='dashboard'),
    path('products/', views.products_view, name='products'),
    path('orders/', views.orders_view, name='orders'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('users/', views.users_view, name='users'),
    path('contacts/', views.contacts_view, name='contacts'),
]
