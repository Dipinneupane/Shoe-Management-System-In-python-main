import json
import requests
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.conf import settings
from .models import Order
from apps.cart.models import Cart
from apps.store.models import Product

@login_required
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    grand_total = sum(item.price * item.quantity for item in cart_items)
    is_success = False

    if request.method == 'POST' and 'order_btn' in request.POST:
        name = request.POST.get('name', '').strip()
        number = request.POST.get('number', '').strip()
        email = request.POST.get('email', '').strip()
        method = 'cod'
        placed_on = datetime.now().strftime('%d-%b-%Y')

        errors = []
        if len(number) != 10 or not number.isdigit():
            errors.append('Phone number must be exactly 10 digits long!')

        user_name = request.user.name or request.user.username
        if user_name and name.lower() != user_name.lower():
            errors.append('Name does not match your account!')

        if request.user.email and email.lower() != request.user.email.lower():
            errors.append('Email does not match your account!')

        if not cart_items.exists():
            errors.append('Your cart is empty!')

        if errors:
            for err in errors:
                messages.error(request, err)
        else:
            cart_products = []
            product_sizes = {}
            for item in cart_items:
                cart_products.append(f"{item.name} ({item.quantity})")
                if item.size:
                    product_sizes[item.name] = item.size

            total_products_str = ", ".join(cart_products)
            sizes_json = json.dumps(product_sizes)

            try:
                with transaction.atomic():
                    # Check stock and update
                    for item in cart_items:
                        prod = Product.objects.select_for_update().filter(name=item.name).first()
                        if not prod:
                            raise ValueError(f"Product '{item.name}' not found.")
                        if prod.quantity < item.quantity:
                            raise ValueError(f"Insufficient stock for '{item.name}'. Only {prod.quantity} left.")
                        prod.quantity -= item.quantity
                        prod.save()

                    # Create order
                    Order.objects.create(
                        user=request.user,
                        name=name,
                        number=number,
                        email=email,
                        method=method,
                        total_products=total_products_str,
                        sizes=sizes_json,
                        total_price=grand_total,
                        placed_on=placed_on,
                        payment_status='pending'
                    )

                    # Clear cart
                    cart_items.delete()
                    is_success = True
                    messages.success(request, 'Order placed successfully!')
            except Exception as e:
                messages.error(request, f"Error placing order: {str(e)}")

    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
        'prefill_name': request.user.name or request.user.username,
        'prefill_email': request.user.email,
        'is_success': is_success,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
def khalti_initiate(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        number = request.POST.get('number', '').strip()
        email = request.POST.get('email', '').strip()

        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'})

        cart_total = sum(float(item.price) * item.quantity for item in cart_items)
        amount_paisa = int(round(cart_total * 100))

        cart_products = [f"{item.name} ({item.quantity})" for item in cart_items]
        product_sizes = {item.name: item.size for item in cart_items if item.size}

        request.session['khalti_order_data'] = {
            'expected_amount': amount_paisa,
            'name': name,
            'number': number,
            'email': email,
            'cart_products': cart_products,
            'product_sizes': product_sizes,
            'cart_total': cart_total,
        }

        purchase_order_id = f"ORD_{request.user.id}_{int(datetime.now().timestamp())}"
        return_url = request.build_absolute_uri('/orders/checkout/khalti-return/')
        website_url = request.build_absolute_uri('/')

        payload = {
            'return_url': return_url,
            'website_url': website_url,
            'amount': amount_paisa,
            'purchase_order_id': purchase_order_id,
            'purchase_order_name': 'Shoe Order',
            'customer_info': {
                'name': name,
                'email': email,
                'phone': number,
            }
        }

        init_url = f"{settings.KHALTI_API_ENDPOINT.rstrip('/')}/epayment/initiate/"
        headers = {
            'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
            'Content-Type': 'application/json',
        }

        try:
            resp = requests.post(init_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if 'payment_url' in data:
                    return JsonResponse({'redirect': data['payment_url']})
                else:
                    return JsonResponse({'success': False, 'message': 'Invalid response from Khalti.'})
            else:
                return JsonResponse({'success': False, 'message': f"Khalti Error ({resp.status_code}): {resp.text}"})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f"Network error: {str(e)}"})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)

@login_required
def khalti_return(request):
    pidx = request.GET.get('pidx', '').strip()
    session_data = request.session.get('khalti_order_data')

    if not pidx or not session_data:
        messages.error(request, 'Missing payment reference or expired session.')
        return redirect('orders:checkout')

    lookup_url = f"{settings.KHALTI_API_ENDPOINT.rstrip('/')}/epayment/lookup/"
    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(lookup_url, json={'pidx': pidx}, headers=headers, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('status', '').lower() == 'completed':
                total_amount = result.get('total_amount', 0)
                expected = session_data.get('expected_amount', 0)

                if total_amount == expected:
                    placed_on = datetime.now().strftime('%d-%b-%Y')
                    cart_items = Cart.objects.filter(user=request.user)

                    with transaction.atomic():
                        for item in cart_items:
                            prod = Product.objects.select_for_update().filter(name=item.name).first()
                            if prod and prod.quantity >= item.quantity:
                                prod.quantity -= item.quantity
                                prod.save()

                        Order.objects.create(
                            user=request.user,
                            name=session_data.get('name'),
                            number=session_data.get('number'),
                            email=session_data.get('email'),
                            method='khalti',
                            total_products=", ".join(session_data.get('cart_products', [])),
                            sizes=json.dumps(session_data.get('product_sizes', {})),
                            total_price=session_data.get('cart_total', 0),
                            placed_on=placed_on,
                            payment_status='completed'
                        )

                        cart_items.delete()
                        request.session.pop('khalti_order_data', None)

                    messages.success(request, 'Khalti Payment successful! Your order has been placed.')
                    return redirect('orders:history')
                else:
                    messages.error(request, 'Amount mismatch during payment verification.')
            else:
                messages.warning(request, f"Payment status: {result.get('status', 'Incomplete')}")
        else:
            messages.error(request, 'Failed to verify payment with Khalti.')
    except Exception as e:
        messages.error(request, f"Verification failed: {str(e)}")

    return redirect('orders:checkout')

@login_required
def order_history(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'orders/orders.html', {'orders': user_orders})

@login_required
def order_details_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return JsonResponse({
        'success': True,
        'order': {
            'id': order.id,
            'name': order.name,
            'number': order.number,
            'email': order.email,
            'method': order.method.upper(),
            'placed_on': order.placed_on,
            'payment_status': order.payment_status.capitalize(),
            'total_price': float(order.total_price),
            'items': order.parsed_items,
        }
    })
