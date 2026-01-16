from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        count = cart.items.count()
    else:
        count = 0
    return {'cart_count': count}