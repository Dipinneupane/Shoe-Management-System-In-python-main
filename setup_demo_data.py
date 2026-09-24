import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shoeproject.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.store.models import Product, Review

User = get_user_model()

print("Setting up initial users...")

# Create Admin User
admin_user = User.objects.filter(email='admin@gmail.com').first()
if not admin_user:
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@gmail.com',
        password='admin123',
        name='Store Admin',
        user_type='admin',
        is_staff=True,
        is_superuser=True
    )
    print("Created Admin: admin@gmail.com / admin123")
else:
    print("Admin already exists.")

# Create Customer User
customer_user = User.objects.filter(email='customer@gmail.com').first()
if not customer_user:
    customer_user = User.objects.create_user(
        username='customer',
        email='customer@gmail.com',
        password='customer123',
        name='Ram Sharma',
        user_type='user'
    )
    print("Created Customer: customer@gmail.com / customer123")
else:
    print("Customer already exists.")

print("\nSetting up sample footwear catalog...")

sample_products = [
    {
        'name': 'Nike Air Max',
        'price': 8500.00,
        'quantity': 15,
        'brand': 'Nike',
        'type': 'Sports',
        'sizes': '39, 40, 41, 42, 43',
        'image': 'Air Max.jpg',
        'description': 'Iconic Nike Air Max cushioning for exceptional daily bounce and athletic training.'
    },
    {
        'name': 'Nike Blazer Mid',
        'price': 7200.00,
        'quantity': 10,
        'brand': 'Nike',
        'type': 'Sneakers',
        'sizes': '40, 41, 42',
        'image': 'nike blazer.jpg',
        'description': 'Vintage basketball classic silhouette with premium suede and leather upper.'
    },
    {
        'name': 'Bata Casual Classic',
        'price': 3200.00,
        'quantity': 25,
        'brand': 'Bata',
        'type': 'Casual',
        'sizes': '38, 39, 40, 41, 42',
        'image': 'bata casual.jpg',
        'description': 'Lightweight everyday slip-on casual shoe offering superior breathability and arch support.'
    },
    {
        'name': 'Bata Executive Oxford',
        'price': 4800.00,
        'quantity': 12,
        'brand': 'Bata',
        'type': 'Formal',
        'sizes': '40, 41, 42, 43',
        'image': 'bata formal.jpg',
        'description': 'Genuine polished leather dress shoe perfect for corporate environments and formal occasions.'
    },
    {
        'name': 'Bata Street Sneaker',
        'price': 2900.00,
        'quantity': 18,
        'brand': 'Bata',
        'type': 'Sneakers',
        'sizes': '39, 40, 41, 42',
        'image': 'bata sneakers.jpg',
        'description': 'Urban street sneaker with grippy vulcanized rubber outsole for skate and city walks.'
    },
    {
        'name': 'Bata Power Sport',
        'price': 3500.00,
        'quantity': 20,
        'brand': 'Bata',
        'type': 'Sports',
        'sizes': '39, 40, 41, 42, 43',
        'image': 'bata sports.jpeg',
        'description': 'High ventilation mesh running shoes engineered for distance running and morning jogging.'
    },
    {
        'name': 'Classic Derby Black',
        'price': 5200.00,
        'quantity': 8,
        'brand': 'Bata',
        'type': 'Formal',
        'sizes': '41, 42, 43',
        'image': 'black formal.jpg',
        'description': 'Sleek and minimalist black leather formal shoe handcrafted with durable stitching.'
    },
    {
        'name': 'Reebok Club Classic',
        'price': 6400.00,
        'quantity': 14,
        'brand': 'Reebok',
        'type': 'Sneakers',
        'sizes': '39, 40, 41, 42',
        'image': 'rebok white.webp',
        'description': 'Timeless low-top court shoes that complement any outfit, featuring cushioned EVA midsole.'
    },
    {
        'name': 'Reebok Flex Trainer',
        'price': 5900.00,
        'quantity': 16,
        'brand': 'Reebok',
        'type': 'Sports',
        'sizes': '40, 41, 42, 43',
        'image': 'rebok shoes.webp',
        'description': 'Versatile cross-training footwear with multi-directional tread and lateral stability cage.'
    },
    {
        'name': 'Rugged Leather Boots',
        'price': 8900.00,
        'quantity': 6,
        'brand': 'Goldstar',
        'type': 'Boots',
        'sizes': '40, 41, 42, 43, 44',
        'image': 'boots.jpg',
        'description': 'Heavy duty ankle-high boots built with water resistant leather and deep lug traction soles.'
    },
    {
        'name': 'Comfort Leather Sandal',
        'price': 2200.00,
        'quantity': 22,
        'brand': 'Bata',
        'type': 'Sandals',
        'sizes': '39, 40, 41, 42',
        'image': 'sandel.jpg',
        'description': 'Contoured anatomical footbed sandal crafted for all-day summer walking ease.'
    },
    {
        'name': 'Monochrome High-Top',
        'price': 4200.00,
        'quantity': 9,
        'brand': 'Converse',
        'type': 'Sneakers',
        'sizes': '38, 39, 40, 41',
        'image': 'high-top.jpg',
        'description': 'Bold canvas high-top shoes featuring signature ankle patch and reinforced toe cap.'
    },
]

created_products = []
for pdata in sample_products:
    p, created = Product.objects.get_or_create(
        name=pdata['name'],
        defaults=pdata
    )
    created_products.append(p)
    if created:
        print(f"Created: {p.name} (Rs {p.price})")
    else:
        print(f"Product exists: {p.name}")

print("\nAdding sample customer reviews...")
if created_products and customer_user:
    sample_reviews = [
        (created_products[0], 5, "Unbelievable comfort! The Air cushioning feels like walking on clouds. Sizing was true to size."),
        (created_products[1], 4, "Great vintage look and pairs nicely with denim. Takes about two days to break in."),
        (created_products[2], 5, "Best budget shoe in Nepal. Excellent durability and super lightweight."),
        (created_products[3], 5, "Very sharp look for office meetings. Premium leather finish."),
        (created_products[7], 4, "Clean aesthetic, very easy to maintain. Highly recommended for daily wear."),
    ]
    for prod, rating, text in sample_reviews:
        rev, created = Review.objects.get_or_create(
            product=prod,
            user=customer_user,
            defaults={'rating': rating, 'review_text': text, 'status': 'approved'}
        )
        if created:
            print(f"Review added for {prod.name}: {rating} stars")

print("\nSetup completed successfully!")
