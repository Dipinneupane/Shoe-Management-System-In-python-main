from django.db import models
from django.conf import settings
from django.db.models import Avg, Count

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)  # Stock quantity
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=50, blank=True, default='')
    brand = models.CharField(max_length=50, blank=True, default='')
    type = models.CharField(max_length=50, blank=True, default='')
    sizes = models.CharField(max_length=200, blank=True, default='')  # Comma-separated sizes e.g. "38, 39, 40"
    image = models.CharField(max_length=255)  # Filename in uploaded_img

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

    @property
    def avg_rating(self):
        avg = self.reviews.filter(status='approved').aggregate(Avg('rating'))['rating__avg']
        return round(float(avg), 1) if avg else 0.0

    @property
    def rating_count(self):
        return self.reviews.filter(status='approved').count()

    @property
    def parsed_sizes(self):
        if not self.sizes:
            return []
        items = []
        for s in self.sizes.split(','):
            s_clean = s.strip()
            if s_clean:
                items.append(s_clean)
        try:
            return sorted(items, key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else x)
        except Exception:
            return items

    @property
    def is_in_stock(self):
        return self.quantity > 0

class Review(models.Model):
    STATUS_CHOICES = (
        ('approved', 'Approved'),
        ('pending', 'Pending'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    review_text = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.product.name} ({self.rating} stars)"
