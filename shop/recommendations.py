from django.db.models import Count, Q, F
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from .models import Product, Order, OrderItem


def get_similar_products(product, limit=4):
    """
    Content-based recommendation: Find similar products based on category, price range.
    """
    if not product:
        return Product.objects.none()
    
    # Calculate price range (±20%)
    price_min = product.price * Decimal('0.8')
    price_max = product.price * Decimal('1.2')
    
    # Get products in same category, excluding current product
    similar = Product.objects.filter(
        category=product.category
    ).exclude(
        id=product.id
    )
    
    # Prioritize products in similar price range
    in_price_range = similar.filter(
        price__gte=price_min,
        price__lte=price_max
    )
    
    # If we have enough in price range, use those; otherwise use all similar
    if in_price_range.count() >= limit:
        return in_price_range[:limit]
    else:
        return similar[:limit]


def get_frequently_bought_together(product, limit=3):
    """
    Collaborative filtering: Find products frequently bought with this product.
    """
    if not product:
        return Product.objects.none()
    
    # Find orders containing this product
    orders_with_product = Order.objects.filter(
        items__product=product
    ).values_list('id', flat=True)
    
    if not orders_with_product:
        # Fallback to similar products if no order history
        return get_similar_products(product, limit)
    
    # Find other products in those orders using OrderItem
    product_ids = OrderItem.objects.filter(
        order_id__in=orders_with_product
    ).exclude(
        product=product
    ).values('product').annotate(
        purchase_count=Count('product')
    ).order_by('-purchase_count')[:limit].values_list('product', flat=True)
    
    # Get the actual Product objects maintaining the order
    products_dict = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    frequently_bought = [products_dict[pid] for pid in product_ids if pid in products_dict]
    
    return frequently_bought


def get_personalized_recommendations(user, limit=6):
    """
    Personalized recommendations based on user's purchase history.
    """
    if not user or not user.is_authenticated:
        return get_trending_products(limit=limit)
    
    # Get user's past purchases (last 90 days)
    ninety_days_ago = timezone.now() - timedelta(days=90)
    user_orders = Order.objects.filter(
        user=user,
        created_at__gte=ninety_days_ago
    )
    
    # Get categories the user has purchased from
    purchased_categories = OrderItem.objects.filter(
        order__in=user_orders
    ).values_list('product__category', flat=True).distinct()
    
    # Get product IDs user already purchased
    purchased_product_ids = OrderItem.objects.filter(
        order__user=user
    ).values_list('product_id', flat=True).distinct()
    
    if not purchased_categories:
        # New user - show trending products
        return get_trending_products(limit=limit)
    
    # Find products in those categories that user hasn't purchased
    # Use direct OrderItem query instead of reverse relation
    product_order_counts = OrderItem.objects.filter(
        product__category__in=purchased_categories
    ).exclude(
        product_id__in=purchased_product_ids
    ).values('product').annotate(
        order_count=Count('order', distinct=True)
    ).order_by('-order_count')
    
    # Get product IDs in order of popularity
    product_ids = [item['product'] for item in product_order_counts]
    
    # Get actual Product objects
    products_dict = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    recommended = [products_dict[pid] for pid in product_ids if pid in products_dict]
    
    # Diversify - max 2 products per category
    diverse_recommendations = []
    category_count = {}
    
    for product in recommended:
        if category_count.get(product.category, 0) < 2:
            diverse_recommendations.append(product)
            category_count[product.category] = category_count.get(product.category, 0) + 1
        
        if len(diverse_recommendations) >= limit:
            break
    
    # If not enough, fill with trending
    if len(diverse_recommendations) < limit:
        trending = get_trending_products(limit=limit - len(diverse_recommendations))
        for product in trending:
            if product not in diverse_recommendations:
                diverse_recommendations.append(product)
    
    return diverse_recommendations[:limit]


def get_trending_products(days=30, limit=8):
    """
    Get trending/popular products based on recent orders.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Use OrderItem to get trending products
    trending_data = OrderItem.objects.filter(
        order__created_at__gte=cutoff_date
    ).values('product').annotate(
        order_count=Count('order', distinct=True),
        total_quantity=Count('id')
    ).annotate(
        popularity_score=F('order_count') * Decimal('1.5') + F('total_quantity')
    ).order_by('-popularity_score')[:limit]
    
    # Get product IDs
    product_ids = [item['product'] for item in trending_data]
    
    # Get actual Product objects maintaining order
    products_dict = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    trending = [products_dict[pid] for pid in product_ids if pid in products_dict]
    
    # If not enough trending products, fill with all products
    if len(trending) < limit:
        additional = Product.objects.exclude(id__in=product_ids)[:limit - len(trending)]
        trending.extend(list(additional))
    
    return trending


def get_recommended_for_you(user, exclude_product=None, limit=6):
    """
    Get personalized recommendations for authenticated users on product detail page.
    """
    if not user or not user.is_authenticated:
        # For anonymous users, show trending products
        recommendations = get_trending_products(limit=limit)
    else:
        recommendations = get_personalized_recommendations(user, limit=limit)
    
    # Exclude current product if specified
    if exclude_product:
        recommendations = [p for p in recommendations if p.id != exclude_product.id]
    
    return recommendations[:limit]
