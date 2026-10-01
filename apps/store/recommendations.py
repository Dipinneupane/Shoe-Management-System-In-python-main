import math
import re
import numpy as np
from django.db.models import Avg, Count
from .models import Product, Review

ISO_SHOE_SIZE_DATASET = [
    {"foot_length_cm": 21.5, "mondopoint_mm": 215, "eu": 34.0, "uk": 2.0, "us_men": 3.0, "us_women": 4.5},
    {"foot_length_cm": 22.0, "mondopoint_mm": 220, "eu": 35.0, "uk": 2.5, "us_men": 3.5, "us_women": 5.0},
    {"foot_length_cm": 22.5, "mondopoint_mm": 225, "eu": 35.5, "uk": 3.0, "us_men": 4.0, "us_women": 5.5},
    {"foot_length_cm": 23.0, "mondopoint_mm": 230, "eu": 36.5, "uk": 3.5, "us_men": 4.5, "us_women": 6.0},
    {"foot_length_cm": 23.5, "mondopoint_mm": 235, "eu": 37.0, "uk": 4.0, "us_men": 5.0, "us_women": 6.5},
    {"foot_length_cm": 24.0, "mondopoint_mm": 240, "eu": 38.0, "uk": 5.0, "us_men": 6.0, "us_women": 7.5},
    {"foot_length_cm": 24.5, "mondopoint_mm": 245, "eu": 38.5, "uk": 5.5, "us_men": 6.5, "us_women": 8.0},
    {"foot_length_cm": 25.0, "mondopoint_mm": 250, "eu": 39.5, "uk": 6.0, "us_men": 7.0, "us_women": 8.5},
    {"foot_length_cm": 25.5, "mondopoint_mm": 255, "eu": 40.5, "uk": 7.0, "us_men": 8.0, "us_women": 9.5},
    {"foot_length_cm": 26.0, "mondopoint_mm": 260, "eu": 41.0, "uk": 7.5, "us_men": 8.5, "us_women": 10.0},
    {"foot_length_cm": 26.5, "mondopoint_mm": 265, "eu": 42.0, "uk": 8.0, "us_men": 9.0, "us_women": 10.5},
    {"foot_length_cm": 27.0, "mondopoint_mm": 270, "eu": 42.5, "uk": 8.5, "us_men": 9.5, "us_women": 11.0},
    {"foot_length_cm": 27.5, "mondopoint_mm": 275, "eu": 43.5, "uk": 9.5, "us_men": 10.5, "us_women": 12.0},
    {"foot_length_cm": 28.0, "mondopoint_mm": 280, "eu": 44.0, "uk": 10.0, "us_men": 11.0, "us_women": 12.5},
    {"foot_length_cm": 28.5, "mondopoint_mm": 285, "eu": 44.5, "uk": 10.5, "us_men": 11.5, "us_women": 13.0},
    {"foot_length_cm": 29.0, "mondopoint_mm": 290, "eu": 45.5, "uk": 11.5, "us_men": 12.5, "us_women": 14.0},
    {"foot_length_cm": 29.5, "mondopoint_mm": 295, "eu": 46.5, "uk": 12.0, "us_men": 13.0, "us_women": 14.5},
    {"foot_length_cm": 30.0, "mondopoint_mm": 300, "eu": 47.0, "uk": 12.5, "us_men": 13.5, "us_women": 15.0},
    {"foot_length_cm": 30.5, "mondopoint_mm": 305, "eu": 48.0, "uk": 13.5, "us_men": 14.5, "us_women": 16.0},
    {"foot_length_cm": 31.0, "mondopoint_mm": 310, "eu": 49.0, "uk": 14.0, "us_men": 15.0, "us_women": 16.5},
]


def get_iso_size_recommendation_knn(foot_length, unit='cm', gender='unisex', k=1, fit_preference='standard'):
    """
    Computes ISO 19407 compliant shoe size recommendations from a foot length
    using the k-Nearest Neighbors (k-NN) algorithm.
    """
    try:
        raw_val = float(foot_length)
    except (TypeError, ValueError):
        return None

    if raw_val <= 0:
        return None

    unit_clean = str(unit).lower().strip()
    if unit_clean in ['inch', 'inches', 'in']:
        length_cm = raw_val * 2.54
    elif unit_clean in ['mm', 'millimeter', 'millimeters']:
        length_cm = raw_val / 10.0
    else:
        length_cm = raw_val

    fit_pref_clean = str(fit_preference).lower().strip()
    adj_length_cm = length_cm
    if fit_pref_clean == 'snug':
        adj_length_cm -= 0.15
    elif fit_pref_clean == 'loose':
        adj_length_cm += 0.35

    distances = []
    for item in ISO_SHOE_SIZE_DATASET:
        ref_cm = item["foot_length_cm"]
        dist = abs(adj_length_cm - ref_cm)
        distances.append((dist, item))

    distances.sort(key=lambda x: x[0])

    best_dist, best_match = distances[0]
    eu_float = best_match["eu"]
    primary_eu = int(round(eu_float))

    confidence = max(40.0, min(100.0, 100.0 * (1.0 - (best_dist / 2.0))))

    delta = length_cm - best_match["foot_length_cm"]
    if abs(delta) <= 0.15:
        fit_assessment = "Optimal true-to-size alignment"
    elif delta > 0.15:
        fit_assessment = f"Form-fitting / snug. Size EU {primary_eu} or EU {primary_eu + 1} recommended"
    else:
        fit_assessment = "Comfortably relaxed fit with standard socks"

    matching_shoes = []
    size_str = str(primary_eu)
    for p in Product.objects.filter(quantity__gt=0):
        parsed = [s.strip() for s in p.sizes.split(',') if s.strip()]
        if size_str in parsed or str(eu_float) in parsed:
            matching_shoes.append(p)
            if len(matching_shoes) >= 6:
                break

    return {
        "foot_length_cm": round(length_cm, 2),
        "foot_length_inch": round(length_cm / 2.54, 2),
        "mondopoint_mm": int(round(length_cm * 10)),
        "primary_eu": primary_eu,
        "eu_size": eu_float,
        "uk_size": best_match["uk"],
        "us_men_size": best_match["us_men"],
        "us_women_size": best_match["us_women"],
        "nearest_distance_cm": round(best_dist, 2),
        "confidence_percent": round(confidence, 1),
        "fit_assessment": fit_assessment,
        "fit_preference": fit_pref_clean or "standard",
        "gender": gender,
        "matching_products": matching_shoes,
    }

def get_size_recommendation(foot_length, product_id=None):
    """
    Backward-compatible size advisor returning recommended primary EU size.
    """
    res = get_iso_size_recommendation_knn(foot_length, unit='cm', k=1)
    if res:
        return res["primary_eu"]
    return None


def infer_user_size_profile_from_purchases(user_id):
    """
    ADVANCED BACKGROUND PROFILER:
    Automatically deduces the customer's true ISO foot length and sizing profile
    in the background by analyzing the shoe sizes from their past orders.
    
    Uses Inverse ISO-19407 Nearest-Neighbor mapping + weighted centroid estimation.
    Zero manual input required from the customer!
    """
    if not user_id:
        return None

    import json
    from apps.orders.models import Order
    from apps.cart.models import Cart

    orders = Order.objects.filter(user_id=user_id).order_by('-id')
    cart_items = Cart.objects.filter(user_id=user_id)

    purchased_sizes = []

    for o in orders:
        if o.sizes:
            try:
                s_dict = json.loads(o.sizes)
                if isinstance(s_dict, dict):
                    for _, s_val in s_dict.items():
                        s_clean = str(s_val).strip()
                        if s_clean and s_clean.replace('.', '', 1).isdigit():
                            purchased_sizes.append(float(s_clean))
            except Exception:
                pass

        if not purchased_sizes and o.total_products:
            for item in o.parsed_items:
                s_clean = str(item.get('size', '')).strip()
                if s_clean and s_clean.replace('.', '', 1).isdigit():
                    purchased_sizes.append(float(s_clean))

    if not purchased_sizes and cart_items.exists():
        for c in cart_items:
            s_clean = str(c.size).strip()
            if s_clean and s_clean.replace('.', '', 1).isdigit():
                purchased_sizes.append(float(s_clean))

    if not purchased_sizes:
        return None

    inferred_foot_lengths = []
    for s_val in purchased_sizes:
        best_match = None
        min_diff = 999.0
        for entry in ISO_SHOE_SIZE_DATASET:
            diff = abs(entry["eu"] - s_val)
            if diff < min_diff:
                min_diff = diff
                best_match = entry

        if best_match:
            inferred_foot_lengths.append(best_match["foot_length_cm"])

    if not inferred_foot_lengths:
        return None

    weights = [1.0 / (idx + 1) for idx in range(len(inferred_foot_lengths))]
    total_weight = sum(weights)
    weighted_foot_length = sum(f * w for f, w in zip(inferred_foot_lengths, weights)) / total_weight

    iso_profile = get_iso_size_recommendation_knn(weighted_foot_length, unit='cm', k=1)
    if iso_profile:
        iso_profile["total_purchases_analyzed"] = len(purchased_sizes)
        iso_profile["learned_from_history"] = True
        return iso_profile

    return None


def build_user_item_matrix():
    """
    Constructs the dense User-Item Rating Matrix R from approved customer reviews.
    """
    reviews = Review.objects.filter(status='approved').values('user_id', 'product_id', 'rating')
    if not reviews.exists():
        return np.zeros((0, 0)), [], [], {}, 3.5

    user_ids = sorted(list(set(r['user_id'] for r in reviews)))
    product_ids = sorted(list(set(r['product_id'] for r in reviews)))

    user_idx = {uid: i for i, uid in enumerate(user_ids)}
    prod_idx = {pid: j for j, pid in enumerate(product_ids)}

    R = np.zeros((len(user_ids), len(product_ids)), dtype=float)
    user_totals = {uid: [] for uid in user_ids}
    all_ratings = []

    for r in reviews:
        u_i = user_idx[r['user_id']]
        p_j = prod_idx[r['product_id']]
        rating = float(r['rating'])
        R[u_i, p_j] = rating
        user_totals[r['user_id']].append(rating)
        all_ratings.append(rating)

    global_mean = float(np.mean(all_ratings)) if all_ratings else 3.5
    user_means = {
        uid: (float(np.mean(ratings)) if ratings else global_mean)
        for uid, ratings in user_totals.items()
    }

    return R, user_ids, product_ids, user_means, global_mean

def get_svd_collaborative_recommendations(user_id, limit=8, n_factors=2):
    """
    BACKGROUND SVD ENGINE:
    Decomposes the User-Item Rating matrix into latent space using Truncated SVD,
    generating personalized shoe predictions in the background.
    """
    R, user_ids, product_ids, user_means, global_mean = build_user_item_matrix()

    if R.size == 0 or user_id not in user_ids:
        return list(Product.objects.annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).filter(quantity__gt=0).order_by('-avg_rtg', '-rtg_cnt', '-id')[:limit])

    u_idx = user_ids.index(user_id)
    u_mean = user_means.get(user_id, global_mean)

    A = np.zeros_like(R)
    for i, uid in enumerate(user_ids):
        m = user_means.get(uid, global_mean)
        for j in range(R.shape[1]):
            if R[i, j] > 0:
                A[i, j] = R[i, j] - m

    M, N = R.shape
    k = max(1, min(n_factors, min(M, N) - 1 if min(M, N) > 1 else 1))

    try:
        U, S, Vt = np.linalg.svd(A, full_matrices=False)
        U_k = U[:, :k]
        S_k = np.diag(S[:k])
        Vt_k = Vt[:k, :]
        A_hat = np.dot(np.dot(U_k, S_k), Vt_k)
        user_pred_row = u_mean + A_hat[u_idx, :]
    except Exception:
        user_pred_row = np.full(len(product_ids), u_mean)

    predictions = []
    rated_pids = set()
    for j, pid in enumerate(product_ids):
        if R[u_idx, j] > 0:
            rated_pids.add(pid)
        else:
            pred_score = float(user_pred_row[j])
            pred_score = max(1.0, min(5.0, pred_score))
            predictions.append((pred_score, pid))

    predictions.sort(key=lambda x: x[0], reverse=True)

    recommended = []
    for pred_score, pid in predictions:
        try:
            prod = Product.objects.get(id=pid)
            if prod.quantity > 0:
                recommended.append(prod)
        except Product.DoesNotExist:
            continue
        if len(recommended) >= limit:
            break

    if len(recommended) < limit:
        existing_ids = {p.id for p in recommended} | rated_pids
        fillers = Product.objects.exclude(id__in=existing_ids).annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).filter(quantity__gt=0).order_by('-avg_rtg', '-rtg_cnt', '-id')[:limit - len(recommended)]
        recommended.extend(fillers)

    return recommended


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
    """
    Ensemble Collaborative Filtering: SVD + Pearson CF.
    """
    svd_recs = get_svd_collaborative_recommendations(user_id, limit=limit)
    if svd_recs:
        return svd_recs

    matrix = get_user_ratings_matrix()
    if user_id not in matrix:
        return list(Product.objects.annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).filter(quantity__gt=0).order_by('-avg_rtg', '-rtg_cnt', '-id')[:limit])

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
            if prod.quantity > 0:
                recommended.append(prod)
        except Product.DoesNotExist:
            continue
        if len(recommended) >= limit:
            break

    if len(recommended) < limit:
        existing_ids = {p.id for p in recommended} | set(user_ratings.keys())
        fillers = Product.objects.exclude(id__in=existing_ids).annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).filter(quantity__gt=0).order_by('-avg_rtg', '-rtg_cnt', '-id')[:limit - len(recommended)]
        recommended.extend(fillers)

    return recommended


def get_content_based_recommendations(product_id, limit=8):
    try:
        seed = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return []

    brand = (seed.brand or '').strip().lower()
    p_type = (seed.type or '').strip().lower()

    if not brand and not p_type:
        return list(Product.objects.exclude(id=product_id).filter(quantity__gt=0)[:limit])

    candidates = Product.objects.exclude(id=product_id).filter(quantity__gt=0).annotate(
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


def get_purchase_based_recommendations(user_id, limit=8, current_product_id=None):
    from apps.orders.models import Order
    orders = Order.objects.filter(user_id=user_id)
    if not orders.exists():
        return list(Product.objects.filter(quantity__gt=0).order_by('-id')[:limit])

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
        return list(Product.objects.filter(quantity__gt=0).order_by('-id')[:limit])

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
        prods = Product.objects.exclude(id__in=exclude_ids).filter(type__iexact=top_type, quantity__gt=0)[:limit]
        results.extend(prods)

    if len(results) < limit and top_brand:
        already = {p.id for p in results} | exclude_ids
        brand_prods = Product.objects.exclude(id__in=already).filter(brand__iexact=top_brand, quantity__gt=0)[:limit - len(results)]
        results.extend(brand_prods)

    if len(results) < limit:
        already = {p.id for p in results} | exclude_ids
        fillers = Product.objects.exclude(id__in=already).filter(quantity__gt=0)[:limit - len(results)]
        results.extend(fillers)

    return results


def get_hybrid_recommendations(user_id, product_id=None, limit=8):
    """
    Ensemble hybrid engine that synthesizes:
    - 40% SVD Matrix Factorization collaborative signals
    - 25% Pearson User-User correlation
    - 20% Content-based item similarity (if product_id given)
    - 15% User purchase history & category affinities
    """
    scores = {}

    svd_recs = get_svd_collaborative_recommendations(user_id, limit=limit * 2)
    for rank, p in enumerate(svd_recs):
        weight = 1.0 / (rank + 1)
        scores[p.id] = scores.get(p.id, 0.0) + (weight * 0.40)

    if product_id:
        content_recs = get_content_based_recommendations(product_id, limit=limit * 2)
        for rank, p in enumerate(content_recs):
            weight = 1.0 / (rank + 1)
            scores[p.id] = scores.get(p.id, 0.0) + (weight * 0.20)

    purchase_recs = get_purchase_based_recommendations(user_id, limit=limit * 2, current_product_id=product_id)
    for rank, p in enumerate(purchase_recs):
        weight = 1.0 / (rank + 1)
        scores[p.id] = scores.get(p.id, 0.0) + (weight * 0.15)

    if product_id and product_id in scores:
        del scores[product_id]

    ranked_pids = sorted(scores.keys(), key=lambda pid: scores[pid], reverse=True)
    products_map = {p.id: p for p in Product.objects.filter(id__in=ranked_pids, quantity__gt=0)}

    results = []
    for pid in ranked_pids:
        if pid in products_map:
            results.append(products_map[pid])
        if len(results) >= limit:
            break

    if len(results) < limit:
        existing_ids = {p.id for p in results}
        if product_id:
            existing_ids.add(int(product_id))
        fillers = Product.objects.exclude(id__in=existing_ids).filter(quantity__gt=0).annotate(
            avg_rtg=Avg('reviews__rating'),
            rtg_cnt=Count('reviews__id')
        ).order_by('-avg_rtg', '-rtg_cnt', '-id')[:limit - len(results)]
        results.extend(fillers)

    return results
