from django.contrib import admin
from .models import Cart

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'price', 'quantity', 'size', 'subtotal')
    list_filter = ('user',)
    search_fields = ('name', 'user__username', 'user__email')
