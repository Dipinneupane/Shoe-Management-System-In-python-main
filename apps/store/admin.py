from django.contrib import admin
from .models import Product, Review

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'type', 'price', 'quantity', 'is_in_stock')
    list_filter = ('brand', 'type')
    search_fields = ('name', 'brand', 'type', 'description')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'status', 'created_at')
    list_filter = ('status', 'rating')
    search_fields = ('product__name', 'user__username', 'user__email', 'review_text')
