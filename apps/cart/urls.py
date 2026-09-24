from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.view_cart, name='cart'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/', views.update_cart, name='update_cart'),
    path('delete/<str:ids>/', views.delete_item, name='delete_item'),
    path('delete-all/', views.delete_all, name='delete_all'),
]
