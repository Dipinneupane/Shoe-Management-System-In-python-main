import os
import re
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.conf import settings
from django.core.files.storage import default_storage
from .decorators import admin_required
from apps.store.models import Product, Review
from apps.orders.models import Order, Message

User = get_user_model()

@admin_required
def dashboard(request):
    total_rev = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_pend = Order.objects.filter(payment_status='pending').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_comp = Order.objects.filter(payment_status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0

    out_of_stock = Product.objects.filter(quantity__lte=0).count()
    pending_reviews = Review.objects.filter(status='pending').count()

    context = {
        'total_revenue': round(float(total_rev), 2),
        'total_pendings': round(float(total_pend), 2),
        'total_completed': round(float(total_comp), 2),
        'out_of_stock_count': out_of_stock,
        'pending_reviews_count': pending_reviews,
        'number_of_orders': Order.objects.count(),
        'number_of_products': Product.objects.count(),
        'number_of_users': User.objects.filter(user_type='user').count(),
        'number_of_admins': User.objects.filter(user_type='admin').count(),
        'total_accounts': User.objects.count(),
        'number_of_messages': Message.objects.count(),
        'today_date': datetime.now().strftime('%A, %B %d, %Y'),
    }
    return render(request, 'store_admin/dashboard.html', context)

@admin_required
def products_view(request):
    # Handle Delete
    delete_id = request.GET.get('delete')
    if delete_id:
        prod = Product.objects.filter(id=delete_id).first()
        if prod:
            if prod.image:
                img_path = os.path.join(settings.MEDIA_ROOT, prod.image)
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass
            prod.delete()
            messages.success(request, 'Product deleted successfully!')
        return redirect('store_admin:products')

    # Handle Edit / Update
    update_id = request.GET.get('update')
    update_product = Product.objects.filter(id=update_id).first() if update_id else None

    if request.method == 'POST':
        # Updating an existing product
        if 'update_product' in request.POST:
            p_id = request.POST.get('update_p_id')
            prod = get_object_or_404(Product, id=p_id)

            prod.name = request.POST.get('update_name', prod.name).strip()
            prod.price = request.POST.get('update_price', prod.price)
            prod.quantity = int(request.POST.get('update_quantity', prod.quantity))
            prod.description = request.POST.get('update_description', prod.description).strip()
            prod.category = request.POST.get('update_category', prod.category).strip()
            prod.brand = request.POST.get('update_brand', prod.brand).strip()
            prod.type = request.POST.get('update_type', prod.type).strip()
            prod.sizes = request.POST.get('update_sizes', prod.sizes).strip()

            new_image = request.FILES.get('update_image')
            if new_image:
                # Remove old file if it exists
                if prod.image:
                    old_path = os.path.join(settings.MEDIA_ROOT, prod.image)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                # Save new file
                filename = new_image.name
                saved_name = default_storage.save(filename, new_image)
                prod.image = os.path.basename(saved_name)

            prod.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('store_admin:products')

        # Adding a new product
        elif 'add_product' in request.POST:
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price', 0)
            quantity = int(request.POST.get('quantity', 0))
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', '').strip()
            brand = request.POST.get('brand', '').strip()
            p_type = request.POST.get('type', '').strip()
            sizes = request.POST.get('sizes', '').strip()
            image_file = request.FILES.get('image')

            if Product.objects.filter(name__iexact=name).exists():
                messages.error(request, 'Product name already exists!')
            elif not image_file:
                messages.error(request, 'Please select a product image!')
            else:
                filename = image_file.name
                saved_name = default_storage.save(filename, image_file)
                base_img_name = os.path.basename(saved_name)

                Product.objects.create(
                    name=name,
                    price=price,
                    quantity=quantity,
                    description=description,
                    category=category,
                    brand=brand,
                    type=p_type,
                    sizes=sizes,
                    image=base_img_name
                )
                messages.success(request, 'Product added successfully!')
                return redirect('store_admin:products')

    filter_stock = request.GET.get('filter')
    qs = Product.objects.all()
    if filter_stock == 'out_of_stock':
        qs = qs.filter(quantity__lte=0)

    return render(request, 'store_admin/products.html', {
        'products': qs,
        'update_product': update_product,
    })

@admin_required
def orders_view(request):
    delete_id = request.GET.get('delete')
    if delete_id:
        Order.objects.filter(id=delete_id).delete()
        messages.success(request, 'Order deleted successfully!')
        return redirect('store_admin:orders')

    if request.method == 'POST' and 'update_order' in request.POST:
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('update_payment', 'pending')
        order = Order.objects.filter(id=order_id).first()
        if order:
            order.payment_status = new_status
            order.save()
            messages.success(request, 'Order payment status updated!')
        return redirect('store_admin:orders')

    orders = Order.objects.all()
    return render(request, 'store_admin/orders.html', {'orders': orders})

@admin_required
def reviews_view(request):
    approve_id = request.GET.get('approve')
    if approve_id:
        Review.objects.filter(id=approve_id).update(status='approved')
        messages.success(request, 'Review approved successfully!')
        return redirect('store_admin:reviews')

    delete_id = request.GET.get('delete')
    if delete_id:
        Review.objects.filter(id=delete_id).delete()
        messages.success(request, 'Review deleted successfully!')
        return redirect('store_admin:reviews')

    reviews = Review.objects.select_related('product', 'user').all()
    return render(request, 'store_admin/reviews.html', {'reviews': reviews})

@admin_required
def users_view(request):
    delete_id = request.GET.get('delete')
    if delete_id:
        target_user = User.objects.filter(id=delete_id).first()
        if target_user:
            is_self = (target_user.id == request.user.id)
            # Cascade delete user reviews
            Review.objects.filter(user=target_user).delete()
            target_user.delete()

            if is_self:
                logout(request)
                request.session['account_deleted'] = True
                return redirect('accounts:login')
            else:
                messages.success(request, 'User account deleted successfully!')
        return redirect('store_admin:users')

    users_list = User.objects.all().order_by('-id')
    return render(request, 'store_admin/users.html', {'users_list': users_list})

@admin_required
def contacts_view(request):
    delete_id = request.GET.get('delete')
    if delete_id:
        Message.objects.filter(id=delete_id).delete()
        messages.success(request, 'Message deleted successfully!')
        return redirect('store_admin:contacts')

    all_messages = Message.objects.all()
    return render(request, 'store_admin/contacts.html', {'messages_list': all_messages})
