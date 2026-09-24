from django.db import models
from django.conf import settings

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=50, blank=True, default='')
    image = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user} - {self.name} (x{self.quantity})"

    @property
    def subtotal(self):
        return self.price * self.quantity
