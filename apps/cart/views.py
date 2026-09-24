from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart
from apps.store.models import Product

@login_required
def view_cart(request):
    raw_items = Cart.objects.filter(user=request.user)
    
    # In-memory grouping matching PHP's cart.php algorithm
    grouped = {}
    grand_total = 0
    
    for item in raw_items:
        size_key = item.size or 'no_size'
        key = f"{item.name}_{size_key}"
        
        prod = Product.objects.filter(name=item.name).first()
        brand = prod.brand if prod else ''
        p_type = prod.type if prod else ''
        
        if key not in grouped:
            grouped[key] = {
                'ids': [item.id],
                'name': item.name,
                'price': float(item.price),
                'quantity': item.quantity,
                'image': item.image,
                'size': item.size,
                'brand': brand,
                'type': p_type,
                'subtotal': float(item.price) * item.quantity,
            }
        else:
            grouped[key]['ids'].append(item.id)
            grouped[key]['quantity'] += item.quantity
            grouped[key]['subtotal'] += float(item.price) * item.quantity
            
    cart_items = list(grouped.values())
    for item in cart_items:
        grand_total += item['subtotal']
        
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'grand_total': round(grand_total, 2),
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = request.POST.get('product_name', product.name)
        product_price = request.POST.get('product_price', product.price)
        product_image = request.POST.get('product_image', product.image)
        quantity = int(request.POST.get('product_quantity', 1))
        size = request.POST.get('product_size', request.POST.get('size', '')).strip()

        if quantity < 1:
            messages.error(request, 'Quantity must be at least 1!')
            return redirect('store:product_detail', product_id=product.id)

        if product.quantity < quantity:
            messages.warning(request, 'Not enough stock available!')
            return redirect('store:product_detail', product_id=product.id)

        existing = Cart.objects.filter(user=request.user, name=product_name, size=size).first()
        if existing:
            messages.warning(request, 'Product with this size is already in your cart!')
        else:
            Cart.objects.create(
                user=request.user,
                name=product_name,
                price=product_price,
                quantity=quantity,
                size=size,
                image=product_image
            )
            messages.success(request, 'Product added to cart!')

    return redirect('store:product_detail', product_id=product.id)

@login_required
def update_cart(request):
    if request.method == 'POST':
        cart_ids_str = request.POST.get('cart_ids', '')
        qty = int(request.POST.get('cart_quantity', request.POST.get('qty', 1)))

        cart_ids = [int(x.strip()) for x in cart_ids_str.split(',') if x.strip().isdigit()]
        if cart_ids:
            primary_id = cart_ids[0]
            item = Cart.objects.filter(id=primary_id, user=request.user).first()
            if item:
                item.quantity = max(1, qty)
                item.save()

                # Clean up any duplicate grouped records
                if len(cart_ids) > 1:
                    Cart.objects.filter(id__in=cart_ids[1:], user=request.user).delete()

                messages.success(request, 'Cart quantity updated!')
    return redirect('cart:cart')

@login_required
def delete_item(request, ids):
    id_list = [int(x.strip()) for x in str(ids).split(',') if x.strip().isdigit()]
    if id_list:
        Cart.objects.filter(id__in=id_list, user=request.user).delete()
        messages.success(request, 'Item(s) removed from cart!')
    return redirect('cart:cart')

@login_required
def delete_all(request):
    Cart.objects.filter(user=request.user).delete()
    messages.success(request, 'Cart emptied successfully!')
    return redirect('cart:cart')
