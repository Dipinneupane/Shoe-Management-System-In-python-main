from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Store Attributes', {'fields': ('name', 'user_type')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Store Attributes', {'fields': ('name', 'user_type')}),
    )
