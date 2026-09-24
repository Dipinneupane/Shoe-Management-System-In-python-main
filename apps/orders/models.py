import json
import re
from django.db import models
from django.conf import settings

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=12)
    email = models.EmailField()
    method = models.CharField(max_length=50)  # 'cod' or 'khalti'
    address = models.CharField(max_length=500, blank=True, default='')
    total_products = models.TextField()  # "Product A (1), Product B (2)"
    sizes = models.TextField(blank=True, default='{}')  # JSON: {"Product A": "42"}
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    placed_on = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, default='pending')  # 'pending', 'completed'

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Order #{self.id} - {self.name} (Rs {self.total_price})"

    @property
    def parsed_items(self):
        """
        Parses total_products string and sizes JSON into structured items list.
        """
        from apps.store.models import Product
        items = []
        sizes_dict = {}
        if self.sizes:
            try:
                sizes_dict = json.loads(self.sizes)
            except Exception:
                sizes_dict = {}

        if self.total_products:
            chunks = [c.strip() for c in self.total_products.split(',') if c.strip()]
            for chunk in chunks:
                m = re.match(r'^(.*?)\s*\((\d+)\)$', chunk)
                if m:
                    p_name = m.group(1).strip()
                    p_qty = int(m.group(2))
                else:
                    p_name = chunk
                    p_qty = 1

                p_size = sizes_dict.get(p_name, '')
                prod = Product.objects.filter(name__iexact=p_name).first()

                items.append({
                    'name': p_name,
                    'quantity': p_qty,
                    'size': p_size,
                    'image': prod.image if prod else '',
                    'brand': prod.brand if prod else '',
                    'type': prod.type if prod else '',
                    'price': float(prod.price) if prod else 0,
                    'subtotal': (float(prod.price) * p_qty) if prod else 0,
                })
        return items

class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    number = models.CharField(max_length=12)
    message = models.TextField()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
