# Happy Fit – Shoe Management & E-Commerce System (Django)

A full-featured footwear e-commerce and store management web application built with Python and Django.

## Features

- **Storefront & Catalog**: Modern footwear showcase with category filtering (Sneakers, Casual, Formal, Sports, Boots, Sandals), search, and detailed product specifications.
- **Smart Recommendation Engine**:
  - Collaborative filtering based on user ratings matrix and Pearson correlation.
  - Content-based recommendations matching footwear type, brand, and attributes.
  - Purchase-history recommendations suggesting next styles based on past customer orders.
  - Foot-length shoe size advisor (cm to EU sizing).
- **Shopping Cart & Checkout**:
  - Multi-item shopping cart with quantity stepper controls.
  - Cash on Delivery (COD) and Khalti payment gateway integration.
  - Real-time inventory tracking and stock depletion on orders.
- **Admin Management Portal**:
  - Dedicated dashboard with key statistics (Revenue, Pending Orders, Inventory, Reviews).
  - Product catalog management (Add, Edit with photo replacement, Stock tracking, Delete).
  - Order status management (Pending / Completed toggle, Delete).
  - Customer review moderation (Approve / Delete).
  - User and customer inquiry message management.

---

## Default Credentials

### Administrator Account
- **Username / Email**: `admin` or `admin@gmail.com`
- **Password**: `admin123`
- **Admin Portal URL**: `http://127.0.0.1:8000/admin-panel/` (or `/admin/`)
- **Django Admin URL**: `http://127.0.0.1:8000/django-admin/`

### Demo Customer Account
- **Username / Email**: `customer` or `customer@gmail.com`
- **Password**: `customer123`
- **Storefront URL**: `http://127.0.0.1:8000/`

---

## Installation & Setup

1. **Clone or navigate to the repository:**
   ```bash
   cd Shoe-Management-System-In-python-main
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Seed initial demo data (products, admin, customer, reviews):**
   ```bash
   python setup_demo_data.py
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   Open your browser at `http://127.0.0.1:8000/`