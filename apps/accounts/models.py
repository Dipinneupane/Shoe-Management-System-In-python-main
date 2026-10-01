from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='user')
    foot_length_cm = models.FloatField(null=True, blank=True, help_text="Foot length in cm")
    shoe_size_preference = models.CharField(max_length=20, blank=True, help_text="Preferred EU size")
    fit_preference = models.CharField(
        max_length=20,
        default='standard',
        choices=(('standard', 'Standard Fit'), ('snug', 'Snug Fit'), ('loose', 'Loose Fit'))
    )

    def save(self, *args, **kwargs):
        if not self.name and (self.first_name or self.last_name):
            self.name = f"{self.first_name} {self.last_name}".strip()
        if self.user_type == 'admin' or self.is_superuser or self.is_staff:
            self.is_staff = True
            self.user_type = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.username or self.email
