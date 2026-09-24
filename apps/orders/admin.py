from django.contrib import admin
from .models import Order, Message

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'number', 'method', 'total_price', 'payment_status', 'placed_on')
    list_filter = ('payment_status', 'method')
    search_fields = ('name', 'email', 'number', 'total_products')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'number', 'user')
    search_fields = ('name', 'email', 'number', 'message')
