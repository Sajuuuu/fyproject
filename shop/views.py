from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order, OrderItem
from userauth.models import Address
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import models
from django.contrib import messages
from .recommendations import (
    get_similar_products,
    get_frequently_bought_together,
    get_trending_products,
    get_personalized_recommendations
)
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
import json
import requests

def send_order_confirmation_email(order):
    """Send HTML order confirmation email to customer"""
    try:
        subject = f'Order Confirmation - #{order.order_number}'
        
        # Get site URL
        site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        
        # Render HTML email
        html_content = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'site_url': site_url,
        })
        
        # Plain text fallback
        text_content = f"""
Dear {order.user.first_name},

Thank you for your order!

Order Details:
Order Number: #{order.order_number}
Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}
Total Amount: NPR {order.total_amount}

Items Ordered:
"""
        for item in order.items.all():
            text_content += f"\n- {item.product.name} x {item.quantity}"
            if item.size:
                text_content += f" (Size: {item.size})"
            text_content += f" - NPR {item.subtotal}"
        
        text_content += f"""

Shipping Address:
{order.first_name} {order.last_name}
{order.address}
{order.city}

We'll send you another email when your order ships.

Thank you for shopping with Pethood!

Best regards,
The Pethood Team
"""
        
        # Create email with HTML
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        return True
    except Exception as e:
        print(f"Failed to send order confirmation email: {e}")
        return False

# Create your views here.
# def shop_home(request):
#     products = Product.objects.all()
#     return render(request, 'shop.html', {'products': products})

def search(request):
    """Search products by name, description, or category"""
    query = request.GET.get('q', '').strip()
    
    if query:
        # Split query into words for better matching
        words = query.split()
        
        # Build query to search for each word
        q_objects = models.Q()
        for word in words:
            q_objects |= (
                models.Q(name__icontains=word) |
                models.Q(description__icontains=word) |
                models.Q(category__icontains=word)
            )
        
        products = Product.objects.filter(q_objects).distinct()
    else:
        products = Product.objects.none()
    
    context = {
        'products': products,
        'query': query,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'search_results.html', context)

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
        payment_method = request.POST.get('payment_method')
        
        # Get address data first (needed for both payment methods)
        saved_address_id = request.POST.get('saved_address_id')
        
        if saved_address_id:
            saved_address = get_object_or_404(Address, id=saved_address_id, user=request.user)
            first_name = request.user.first_name or request.user.username
            last_name = request.user.last_name or ''
            email = request.user.email
            phone = saved_address.phone
            address = saved_address.address_line
            city = saved_address.city
            postal_code = saved_address.postal_code
        else:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            city = request.POST.get('city')
            postal_code = request.POST.get('postal_code')
        
        # Store billing details in session for Khalti callback
        billing_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'address': address,
            'city': city,
            'postal_code': postal_code,
            'saved_address_id': saved_address_id,
        }
        request.session['khalti_billing'] = billing_data
        
        if payment_method == 'khalti':
            # Initiate Khalti payment on server-side
            purchase_order_id = f"ORDER-{request.user.id}-{cart.id}"
            request.session['purchase_order_id'] = purchase_order_id
            
            amount_in_paisa = int(grand_total * 100)
            
            headers = {
                "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "return_url": request.build_absolute_uri('/khalti-callback/'),
                "website_url": request.build_absolute_uri('/'),
                "amount": amount_in_paisa,
                "purchase_order_id": purchase_order_id,
                "purchase_order_name": "Pethood Order",
                "customer_info": {
                    "name": f"{first_name} {last_name}",
                    "email": email,
                    "phone": phone
                }
            }
            
            try:
                response = requests.post(
                    settings.KHALTI_INITIATE_URL,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    payment_url = response_data.get('payment_url')
                    
                    if payment_url:
                        # Redirect user to Khalti payment page
                        return redirect(payment_url)
                    else:
                        # Payment URL not found in response
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
                            'error': 'Failed to initialize payment. Please try again.'
                        }
                        return render(request, 'checkout.html', context)
                else:
                    # Payment initiation failed
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
                        'error': f'Payment initiation failed: {response.text}'
                    }
                    return render(request, 'checkout.html', context)
            except Exception as e:
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
                    'error': f'Payment error: {str(e)}'
                }
                return render(request, 'checkout.html', context)
        
        # Handle COD orders
        elif payment_method == 'cod':
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
            
            # Send order confirmation email
            send_order_confirmation_email(order)
            
            # Store order ID in session for order_success page
            request.session['last_order_id'] = order.id
            
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


# Khalti callback handler (new KPG-2 API)
@login_required
def khalti_callback(request):
    # Get callback parameters
    pidx = request.GET.get('pidx')
    status = request.GET.get('status')
    transaction_id = request.GET.get('transaction_id')
    purchase_order_id = request.GET.get('purchase_order_id')
    amount = request.GET.get('amount')
    
    # Verify payment using lookup API
    headers = {
        "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {"pidx": pidx}
    
    try:
        response = requests.post(
            settings.KHALTI_VERIFY_URL.replace('payment/verify', 'epayment/lookup'),
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            verification_data = response.json()
            
            # Only create order if status is "Completed"
            if verification_data.get('status') == 'Completed':
                # Get billing info from session
                billing = request.session.get('khalti_billing', {})
                
                # Get cart items
                cart = Cart.objects.get(user=request.user)
                buy_now_item_id = request.session.get('buy_now_item_id')
                
                if buy_now_item_id:
                    items = cart.items.filter(id=buy_now_item_id)
                else:
                    items = cart.items.all()
                
                # Calculate total
                total = sum(item.product.price * item.quantity for item in items)
                grand_total = total + 5  # shipping
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=billing.get('first_name', request.user.first_name),
                    last_name=billing.get('last_name', request.user.last_name),
                    email=billing.get('email', request.user.email),
                    phone=billing.get('phone'),
                    address=billing.get('address'),
                    city=billing.get('city'),
                    postal_code=billing.get('postal_code', ''),
                    notes=billing.get('notes', ''),
                    total_amount=grand_total,
                    payment_method='khalti',
                    payment_verified=True,
                    khalti_transaction_id=transaction_id,
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
                
                # Send order confirmation email
                send_order_confirmation_email(order)
                
                # Save address if needed
                saved_address_id = billing.get('saved_address_id')
                if not saved_address_id and Address.objects.filter(user=request.user).count() < 3:
                    Address.objects.create(
                        user=request.user,
                        label='Delivery Address',
                        address_line=billing.get('address'),
                        city=billing.get('city'),
                        postal_code=billing.get('postal_code', ''),
                        phone=billing.get('phone'),
                        is_default=Address.objects.filter(user=request.user).count() == 0
                    )
                
                # Clear cart items
                items.delete()
                
                # Store order ID in session for order_success page
                request.session['last_order_id'] = order.id
                
                # Clear session data
                if 'buy_now_item_id' in request.session:
                    del request.session['buy_now_item_id']
                if 'khalti_billing' in request.session:
                    del request.session['khalti_billing']
                if 'purchase_order_id' in request.session:
                    del request.session['purchase_order_id']
                
                return redirect('order_success')
            else:
                # Payment not completed
                return render(request, 'payment_failed.html', {
                    'status': verification_data.get('status'),
                    'message': f"Payment {verification_data.get('status')}. Please try again."
                })
        else:
            return render(request, 'payment_failed.html', {
                'message': 'Payment verification failed. Please contact support.'
            })
            
    except Exception as e:
        return render(request, 'payment_failed.html', {
            'message': f'Error: {str(e)}'
        })


# Order success page
@login_required
def order_success(request):
    try:
        # Get the order from session
        order_id = request.session.get('last_order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                # Clear the session variable after retrieving
                if 'last_order_id' in request.session:
                    del request.session['last_order_id']
                return render(request, 'order_success.html', {'order': order})
            except Order.DoesNotExist:
                print(f"Order with id {order_id} not found for user {request.user.username}")
                pass
        
        # Fallback: Get the latest order for this user
        order = Order.objects.filter(user=request.user).order_by('-created_at').first()
        if not order:
            messages.error(request, 'No order found.')
            return redirect('shop_home')
        return render(request, 'order_success.html', {'order': order})
    except Exception as e:
        print(f"Error in order_success view: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'An error occurred while displaying your order.')
        return redirect('shop_home')

@login_required
def cancel_order(request, order_id):
    """Cancel an order if it's still pending"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow cancellation if order is pending (before packing)
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order #{order.order_number} has been cancelled successfully.')
    else:
        messages.error(request, f'Order #{order.order_number} cannot be cancelled as it is already {order.get_status_display().lower()}.')
    
    return redirect('profile')




