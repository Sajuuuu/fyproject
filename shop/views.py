from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

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

def productdetails(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'productdetails.html', {'product': product})


# AJAX Add to Cart
@login_required
def add_to_cart_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Get the size from the AJAX request
    data = json.loads(request.body)
    selected_size = data.get('size', None)

    # Get or create cart item with same product AND size
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=selected_size  # Save the size here
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({
        'success': True,
        'cart_count': cart.items.count(),
        'product_name': product.name,
    })
    
# Cart page
@login_required
def cart_view(request):
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


