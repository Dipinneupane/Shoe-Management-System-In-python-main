import math
import re
from django.db.models import Avg, Count
from .models import Product, Review

def get_content_based_recommendations(product_id, limit=8):
    try:
        seed = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return []

    brand = (seed.brand or '').strip().lower()
    p_type = (seed.type or '').strip().lower()

    if not brand and not p_type:
        return list(Product.objects.exclude(id=product_id).filter(quantity__gt=0)[:limit])

    candidates = Product.objects.exclude(id=product_id).annotate(
        avg_rtg=Avg('reviews__rating'),
        rtg_cnt=Count('reviews__id')
    )

    scored = []
    for p in candidates:
        p_b = (p.brand or '').strip().lower()
        p_t = (p.type or '').strip().lower()

        score = 0
        if brand and p_type and p_b == brand and p_t == p_type:
            score += 2
        else:
            if brand and p_b == brand:
                score += 1
            if p_type and p_t == p_type:
                score += 1

        if score <= 0:
            continue

        avg_val = float(p.avg_rtg or 0)
        cnt_val = int(p.rtg_cnt or 0)
        score += (avg_val * 0.5) + (cnt_val * 0.05)
        scored.append((score, p))

    scored.sort(key=lambda x: (x[0], x[1].id), reverse=True)
    return [item[1] for item in scored[:limit]]

def get_user_ratings_matrix():
    reviews = Review.objects.filter(status='approved').values('user_id', 'product_id', 'rating')
    matrix = {}
    for r in reviews:
        u_id = r['user_id']
        p_id = r['product_id']
        rating = float(r['rating'])
        if u_id not in matrix:
            matrix[u_id] = {}
        matrix[u_id][p_id] = rating
    return matrix

def pearson_correlation(ratings1, ratings2):
    common = set(ratings1.keys()) & set(ratings2.keys())
    n = len(common)
    if n == 0:
        return 0.0

    sum1 = sum(ratings1[p] for p in common)
    sum2 = sum(ratings2[p] for p in common)

    sum1_sq = sum(ratings1[p] ** 2 for p in common)
    sum2_sq = sum(ratings2[p] ** 2 for p in common)

    p_sum = sum(ratings1[p] * ratings2[p] for p in common)

    num = p_sum - (sum1 * sum2 / n)
    den = math.sqrt((sum1_sq - (sum1 ** 2 / n)) * (sum2_sq - (sum2 ** 2 / n)))
    if den == 0:
        return 0.0
    return num / den

def get_collaborative_recommendations(user_id, limit=8):
    matrix = get_user_ratings_matrix()
    if user_id not in matrix:
        # Fallback to top rated products
        return list(Product.objects.annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).order_by('-avg_rtg', '-rtg_cnt')[:limit])

    user_ratings = matrix[user_id]
    scores = {}
    sim_sums = {}

    for other_user_id, other_ratings in matrix.items():
        if other_user_id == user_id:
            continue

        sim = pearson_correlation(user_ratings, other_ratings)
        if sim <= 0:
            continue

        for p_id, rating in other_ratings.items():
            if p_id not in user_ratings:
                scores[p_id] = scores.get(p_id, 0.0) + (rating * sim)
                sim_sums[p_id] = sim_sums.get(p_id, 0.0) + sim

    predictions = []
    for p_id, total_score in scores.items():
        if sim_sums[p_id] > 0:
            pred_rating = total_score / sim_sums[p_id]
            predictions.append((pred_rating, p_id))

    predictions.sort(key=lambda x: x[0], reverse=True)

    recommended = []
    for pred_rating, p_id in predictions:
        try:
            prod = Product.objects.get(id=p_id)
            if prod.rating_count > 0 and prod.avg_rating < 3.0:
                continue
            recommended.append(prod)
        except Product.DoesNotExist:
            continue
        if len(recommended) >= limit:
            break

    if len(recommended) < limit:
        # Fill with top popular products
        existing_ids = {p.id for p in recommended} | set(user_ratings.keys())
        fillers = Product.objects.exclude(id__in=existing_ids).annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).order_by('-avg_rtg', '-rtg_cnt')[:limit - len(recommended)]
        recommended.extend(fillers)

    return recommended

def get_purchase_based_recommendations(user_id, limit=8, current_product_id=None):
    from apps.orders.models import Order
    orders = Order.objects.filter(user_id=user_id)
    if not orders.exists():
        return list(Product.objects.all().order_by('-id')[:limit])

    name_qty = {}
    for o in orders:
        parts = re.split(r'[;,\n]+', o.total_products or '')
        for chunk in parts:
            chunk = chunk.strip()
            if not chunk:
                continue
            qty = 1
            m = re.search(r'\((\d+)\)', chunk)
            if m:
                qty = max(1, int(m.group(1)))
            clean_name = re.sub(r'\s*\(\d+\)\s*', '', chunk)
            clean_name = re.sub(r'-\s*\d+[\.,]?\d*', '', clean_name)
            clean_name = re.sub(r'Rs\s*\d+[\.,]?\d*', '', clean_name, flags=re.I).strip(' -')
            if clean_name:
                name_qty[clean_name] = name_qty.get(clean_name, 0) + qty

    if not name_qty:
        return list(Product.objects.all().order_by('-id')[:limit])

    exclude_ids = set()
    if current_product_id:
        exclude_ids.add(int(current_product_id))

    type_counts = {}
    brand_counts = {}

    for name, qty in name_qty.items():
        found = Product.objects.filter(name__iexact=name).first()
        if not found:
            found = Product.objects.filter(name__icontains=name).first()
        if found:
            exclude_ids.add(found.id)
            if found.type:
                type_counts[found.type] = type_counts.get(found.type, 0) + qty
            if found.brand:
                brand_counts[found.brand] = brand_counts.get(found.brand, 0) + qty

    top_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
    top_brand = max(brand_counts.items(), key=lambda x: x[1])[0] if brand_counts else None

    results = []
    if top_type:
        prods = Product.objects.exclude(id__in=exclude_ids).filter(type__iexact=top_type)[:limit]
        results.extend(prods)

    if len(results) < limit and top_brand:
        already = {p.id for p in results} | exclude_ids
        brand_prods = Product.objects.exclude(id__in=already).filter(brand__iexact=top_brand)[:limit - len(results)]
        results.extend(brand_prods)

    if len(results) < limit:
        already = {p.id for p in results} | exclude_ids
        fillers = Product.objects.exclude(id__in=already)[:limit - len(results)]
        results.extend(fillers)

    return results

def get_size_recommendation(foot_length, product_id=None):
    """
    Standard shoe sizing advisor based on foot length in cm.
    e.g. 24.5cm -> EU 39
    """
    try:
        length = float(foot_length)
    except (TypeError, ValueError):
        return None

    # Conversion chart approximation: EU size = (length in cm + 1.5) * 1.5
    estimated_eu = round((length + 1.5) * 1.5)
    return estimated_eu
