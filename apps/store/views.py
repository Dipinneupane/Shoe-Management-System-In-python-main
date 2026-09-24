from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from .models import Product, Review
from apps.cart.models import Cart
from apps.orders.models import Message, Order
from .recommendations import (
    get_content_based_recommendations,
    get_collaborative_recommendations,
    get_purchase_based_recommendations,
    get_size_recommendation,
)

@login_required
def home(request):
    if request.method == 'POST' and 'add_to_cart' in request.POST:
        product_name = request.POST.get('product_name')
        product_price = request.POST.get('product_price')
        product_image = request.POST.get('product_image')
        product_quantity = int(request.POST.get('product_quantity', 1))

        existing = Cart.objects.filter(user=request.user, name=product_name).first()
        if existing:
            messages.warning(request, 'Already added to cart!')
        else:
            Cart.objects.create(
                user=request.user,
                name=product_name,
                price=product_price,
                quantity=product_quantity,
                image=product_image
            )
            messages.success(request, 'Product added to cart!')
        return redirect('store:home')

    # Collaborative Recommendations
    collaborative_recs = get_collaborative_recommendations(request.user.id, 8)

    # Latest Products with Ratings
    latest_products = Product.objects.annotate(
        avg_rtg=Avg('reviews__rating'),
        rtg_cnt=Count('reviews__id')
    ).order_by('-avg_rtg', '-rtg_cnt', '-id')[:6]

    # Purchase-Based Recommendations
    purchase_recs = get_purchase_based_recommendations(request.user.id, 8)

    # Most Reviewed Products
    most_reviewed = Product.objects.annotate(
        review_count=Count('reviews__id'),
        avg_rtg=Avg('reviews__rating')
    ).filter(review_count__gt=0).order_by('-review_count', '-avg_rtg')[:4]

    # Testimonials Slider (approved reviews with rating >= 4)
    testimonials = Review.objects.filter(status='approved', rating__gte=4).select_related('user', 'product')[:5]

    # Foot Length Advisor
    foot_length = request.session.get('foot_length')
    recommended_size = get_size_recommendation(foot_length) if foot_length else None

    context = {
        'collaborative_recs': collaborative_recs,
        'latest_products': latest_products,
        'purchase_recs': purchase_recs,
        'most_reviewed_products': most_reviewed,
        'testimonials': testimonials,
        'recommended_size': recommended_size,
    }
    return render(request, 'store/home.html', context)

@login_required
def about(request):
    testimonials = Review.objects.filter(status='approved').select_related('user', 'product')[:5]
    return render(request, 'store/about.html', {'testimonials': testimonials})

@login_required
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        number = request.POST.get('number', '').strip()
        msg_text = request.POST.get('message', '').strip()

        if len(number) != 10 or not number.isdigit():
            messages.error(request, 'Phone number must be exactly 10 digits!')
            return redirect('store:contact')

        if Message.objects.filter(name=name, email=email, number=number, message=msg_text).exists():
            messages.warning(request, 'Message already sent!')
        else:
            Message.objects.create(
                user=request.user,
                name=name,
                email=email,
                number=number,
                message=msg_text
            )
            messages.success(request, 'Message sent successfully!')
        return redirect('store:contact')

    return render(request, 'store/contact.html')

@login_required
def search_page(request):
    query = request.GET.get('search', request.POST.get('search', '')).strip()

    if request.method == 'POST' and 'add_to_cart' in request.POST:
        product_name = request.POST.get('product_name')
        product_price = request.POST.get('product_price')
        product_image = request.POST.get('product_image')
        product_quantity = int(request.POST.get('product_quantity', 1))

        if Cart.objects.filter(user=request.user, name=product_name).exists():
            messages.warning(request, 'Already added to cart!')
        else:
            Cart.objects.create(
                user=request.user,
                name=product_name,
                price=product_price,
                quantity=product_quantity,
                image=product_image
            )
            messages.success(request, 'Product added to cart!')
        return redirect(f"{request.path}?search={query}")

    products = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(type__icontains=query)
        ).annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).order_by('-id')

    return render(request, 'store/search.html', {'products': products, 'search_query': query})

@login_required
def shop(request):
    if request.method == 'POST' and 'add_to_cart' in request.POST:
        product_name = request.POST.get('product_name')
        product_price = request.POST.get('product_price')
        product_image = request.POST.get('product_image')
        product_quantity = int(request.POST.get('product_quantity', 1))

        if Cart.objects.filter(user=request.user, name=product_name).exists():
            messages.warning(request, 'Already added to cart!')
        else:
            Cart.objects.create(
                user=request.user,
                name=product_name,
                price=product_price,
                quantity=product_quantity,
                image=product_image
            )
            messages.success(request, 'Product added to cart!')
        return redirect(request.get_full_path())

    search_query = request.GET.get('search', '').strip()
    brand_filter = request.GET.get('brand', '').strip()
    type_filter = request.GET.get('type', '').strip()

    qs = Product.objects.all()
    if search_query:
        qs = qs.filter(Q(name__icontains=search_query) | Q(brand__icontains=search_query) | Q(type__icontains=search_query))
    if brand_filter:
        qs = qs.filter(brand__iexact=brand_filter)
    if type_filter:
        qs = qs.filter(type__iexact=type_filter)

    products = qs.annotate(
        avg_rtg=Avg('reviews__rating'),
        rtg_cnt=Count('reviews__id')
    ).order_by('-avg_rtg', '-rtg_cnt', '-id')

    return render(request, 'store/shop.html', {
        'products': products,
        'search_query': search_query,
        'brand_filter': brand_filter,
        'type_filter': type_filter
    })

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.filter(status='approved').select_related('user')
    recommendations = get_content_based_recommendations(product.id, 8)

    user_review = product.reviews.filter(user=request.user).first()
    has_purchased = Order.objects.filter(user=request.user, total_products__icontains=product.name).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'recommendations': recommendations,
        'user_review': user_review,
        'has_purchased': has_purchased,
    }
    return render(request, 'store/product.html', context)

@login_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        review_text = request.POST.get('review_text', '').strip()

        review_obj, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'review_text': review_text,
                'status': 'approved'
            }
        )
        if created:
            messages.success(request, 'Thank you for your review! It is now visible.')
        else:
            messages.success(request, 'Your review has been updated successfully!')

    return redirect('store:product_detail', product_id=product.id)
