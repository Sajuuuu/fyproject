from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order, OrderItem
from userauth.models import Address
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .recommendations import (
    get_similar_products,
    get_frequently_bought_together,
    get_trending_products,
    get_personalized_recommendations
)
import json
import requests

# Create your views here.
# def shop_home(request):
#     products = Product.objects.all()
#     return render(request, 'shop.html', {'products': products})


def shop_home(request):
    selected_categories = request.GET.getlist('category')
    sort_option = request.GET.get('sort')
    selected_size = request.GET.get('size')  # optional size filter

    products = Product.objects.all()

    # Filter by category
    if selected_categories and "all" not in selected_categories:
        products = products.filter(category__in=selected_categories)

    # Filter by size (only applies to Clothes/Accessories)
    if selected_size:
        products = products.filter(sizes__name=selected_size)

    # Sorting
    if sort_option == "price_low":
        products = products.order_by('price')
    elif sort_option == "price_high":
        products = products.order_by('-price')

    context = {
        "products": products,
        "categories": Product.CATEGORY_CHOICES,
        "selected_categories": selected_categories,
        
    }
    return render(request, "shop.html", context)

def productdetails(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    # Get cart items for logged-in users to check if product+size combo exists
    cart_items_in_cart = []
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Get all cart items for this product with their sizes
        cart_items = CartItem.objects.filter(cart=cart, product=product)
        cart_items_in_cart = [item.size for item in cart_items]
    
    # Get recommendations
    similar_products = get_similar_products(product, limit=4)
    frequently_bought = get_frequently_bought_together(product, limit=3)
    
    return render(request, 'productdetails.html', {
        'product': product,
        'cart_items_in_cart': cart_items_in_cart,
        'similar_products': similar_products,
        'frequently_bought': frequently_bought,
    })


# AJAX Add to Cart
def add_to_cart_ajax(request, product_id):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'redirect': '/login/'})
    
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get the size from the AJAX request
    data = json.loads(request.body)
    selected_size = data.get('size', None)

    # Check if cart item with same product AND size already exists
    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
        size=selected_size
    ).first()

    if cart_item:
        # Item already exists in cart - don't allow adding again
        return JsonResponse({
            'success': False,
            'already_in_cart': True,
            'message': 'This item is already in your cart',
        })
    
    # Create new cart item
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        size=selected_size,
        quantity=1
    )

    return JsonResponse({
        'success': True,
        'cart_count': cart.items.count(),
        'product_name': product.name,
    })


# Buy Now - Add to cart and redirect to checkout
def buy_now_ajax(request, product_id):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'redirect': '/login/'})
    
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get the size from the AJAX request
    data = json.loads(request.body)
    selected_size = data.get('size', None)

    # Get or create cart item with same product AND size
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=selected_size
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Store the specific cart item ID in session for buy now
    request.session['buy_now_item_id'] = cart_item.id

    # Redirect to checkout
    return JsonResponse({
        'success': True,
        'redirect': '/checkout/'
    })
    
# Cart page
@login_required
def cart_view(request):
    # Clear buy_now_item_id from session when viewing full cart
    # This ensures normal checkout flow works for all items
    if 'buy_now_item_id' in request.session:
        del request.session['buy_now_item_id']
    
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.all()
    total = cart.total_price()
    cart_count = cart.items.count() 
    return render(request, 'cart.html', {'cart': cart, 'items': items, 'total': total, 'cart_count': cart_count,})


# Update item quantity

@login_required
@require_POST
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    # Update quantity
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
    else:
        item.delete()
        return redirect('cart_view')

    # Update size if passed in the form
    new_size = request.POST.get('size')
    if new_size:
        item.size = new_size

    item.save()
    return redirect('cart_view')



# Remove item from cart
@login_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart_view')


# Checkout page
@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Check if this is a "Buy Now" checkout (only checkout specific item)
    buy_now_item_id = request.session.get('buy_now_item_id')
    
    if buy_now_item_id:
        # Only checkout the specific item from buy now
        items = cart.items.filter(id=buy_now_item_id)
    else:
        # Regular checkout - show all cart items
        items = cart.items.all()
    
    if not items.exists():
        return redirect('cart_view')
    
    # Get user's saved addresses
    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()
    
    # Calculate total only for items being checked out
    total = sum(item.product.price * item.quantity for item in items)
    shipping = 5
    grand_total = total + shipping
    
    if request.method == 'POST':
        # Handle COD orders
        payment_method = request.POST.get('payment_method')
        
        # Get address data (either from saved address or manual input)
        saved_address_id = request.POST.get('saved_address_id')
        
        if saved_address_id:
            # Use saved address
            saved_address = get_object_or_404(Address, id=saved_address_id, user=request.user)
            first_name = request.user.first_name or request.user.username
            last_name = request.user.last_name or ''
            email = request.user.email
            phone = saved_address.phone
            address = saved_address.address_line
            city = saved_address.city
            postal_code = saved_address.postal_code
        else:
            # Use manual input
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            postal_code = request.POST.get('postal_code', '')
            
            # Save new address to user's profile if they don't have 3 addresses yet
            save_address = request.POST.get('save_address')  # Optional checkbox
            if save_address or Address.objects.filter(user=request.user).count() == 0:
                # Only save if user has less than 3 addresses
                if Address.objects.filter(user=request.user).count() < 3:
                    # Check if this exact address already exists
                    existing = Address.objects.filter(
                        user=request.user,
                        address_line=address,
                        city=city,
                        phone=phone
                    ).first()
                    
                    if not existing:
                        Address.objects.create(
                            user=request.user,
                            label='Delivery Address',
                            address_line=address,
                            city=city,
                            postal_code=postal_code,
                            phone=phone,
                            is_default=Address.objects.filter(user=request.user).count() == 0
                        )
        
        if payment_method == 'cod':
            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                postal_code=postal_code,
                notes=request.POST.get('notes', ''),
                total_amount=grand_total,
                payment_method='cod',
                status='pending'
            )
            
            # Create order items
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    size=item.size,
                    price=item.product.price
                )
            
            # Clear the checked out items
            items.delete()
            
            # Clear buy now session flag
            if 'buy_now_item_id' in request.session:
                del request.session['buy_now_item_id']
            
            return redirect('order_success')
    
    context = {
        'items': items,
        'total': total,
        'shipping': shipping,
        'grand_total': grand_total,
        'cart': cart,
        'cart_count': items.count(),
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY,
        'addresses': addresses,
        'default_address': default_address,
        'is_buy_now': buy_now_item_id is not None,
    }
    return render(request, 'checkout.html', context)


# Khalti payment verification
@login_required
@require_POST
def khalti_verify(request):
    data = json.loads(request.body)
    token = data.get('token')
    amount = data.get('amount')
    billing_info = data.get('billing_info')
    saved_address_id = data.get('saved_address_id')
    
    # Verify payment with Khalti
    url = settings.KHALTI_VERIFY_URL
    payload = {
        "token": token,
        "amount": amount
    }
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('idx'):
            # Payment verified, create order
            cart = Cart.objects.get(user=request.user)
            
            # Check if this is a buy now checkout
            buy_now_item_id = request.session.get('buy_now_item_id')
            if buy_now_item_id:
                items = cart.items.filter(id=buy_now_item_id)
            else:
                items = cart.items.all()
            
            # Calculate total for items being checked out
            total = sum(item.product.price * item.quantity for item in items) + 5  # Include shipping
            
            # Get address data
            if saved_address_id:
                saved_address = Address.objects.get(id=saved_address_id, user=request.user)
                first_name = request.user.first_name or request.user.username
                last_name = request.user.last_name or ''
                email = request.user.email
                phone = saved_address.phone
                address = saved_address.address_line
                city = saved_address.city
                postal_code = saved_address.postal_code
            else:
                first_name = billing_info.get('first_name')
                last_name = billing_info.get('last_name')
                email = billing_info.get('email')
                phone = billing_info.get('phone')
                address = billing_info.get('address')
                city = billing_info.get('city')
                postal_code = billing_info.get('postal_code', '')
                
                # Save new address to user's profile
                if Address.objects.filter(user=request.user).count() < 3:
                    # Check if this exact address already exists
                    existing = Address.objects.filter(
                        user=request.user,
                        address_line=address,
                        city=city,
                        phone=phone
                    ).first()
                    
                    if not existing:
                        Address.objects.create(
                            user=request.user,
                            label='Delivery Address',
                            address_line=address,
                            city=city,
                            postal_code=postal_code,
                            phone=phone,
                            is_default=Address.objects.filter(user=request.user).count() == 0
                        )
            
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                postal_code=postal_code,
                notes=billing_info.get('notes', ''),
                total_amount=total,
                payment_method='khalti',
                payment_verified=True,
                khalti_token=token,
                khalti_transaction_id=response_data.get('idx'),
                status='processing'
            )
            
            # Create order items
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    size=item.size,
                    price=item.product.price
                )
            
            # Clear the checked out items
            items.delete()
            
            # Clear buy now session flag
            if 'buy_now_item_id' in request.session:
                del request.session['buy_now_item_id']
            
            return JsonResponse({'success': True, 'order_id': order.id})
        else:
            return JsonResponse({'success': False, 'message': 'Payment verification failed'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# Order success page
@login_required
def order_success(request):
    # Get the latest order for this user
    order = Order.objects.filter(user=request.user).first()
    return render(request, 'order_success.html', {'order': order})



