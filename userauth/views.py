from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Address
from shop.recommendations import get_trending_products, get_personalized_recommendations

# Create your views here.
def home(request):
    # Get trending products
    trending_products = get_trending_products(days=30, limit=8)
    
    # Get personalized recommendations for authenticated users
    if request.user.is_authenticated:
        recommended_products = get_personalized_recommendations(request.user, limit=6)
    else:
        recommended_products = None
    
    return render(request, 'home.html', {
        'trending_products': trending_products,
        'recommended_products': recommended_products,
    })

def signinpage(request):
    error_message = None
   
    if request.method == 'POST':
        uname = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            error_message = "Your password and confirm password are not the same!"
        elif User.objects.filter(username__iexact=uname).exists():
            error_message = "Username already exists!"
        elif User.objects.filter(email__iexact=email).exists():
            error_message = "Email already exists!"
        else:
            myuser = User.objects.create_user(username=uname, email=email, password=pass1)
            myuser.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')

    return render(request, 'signup.html', {'error_message': error_message})

def loginpage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect after successful login
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

def logout_view(request):
    logout(request)  # clears session
    return redirect('home')  # redirect wherever you want


# Profile and Address Management
@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    can_add_more = addresses.count() < 3
    
    context = {
        'addresses': addresses,
        'can_add_more': can_add_more
    }
    return render(request, 'profile.html', context)


@login_required
def add_address(request):
    if request.method == 'POST':
        # Check if user already has 3 addresses
        if Address.objects.filter(user=request.user).count() >= 3:
            messages.error(request, 'You can only have up to 3 saved addresses.')
            return redirect('profile')
        
        try:
            address = Address.objects.create(
                user=request.user,
                label=request.POST.get('label'),
                address_line=request.POST.get('address_line'),
                city=request.POST.get('city'),
                postal_code=request.POST.get('postal_code', ''),
                phone=request.POST.get('phone'),
                is_default=request.POST.get('is_default') == 'on'
            )
            messages.success(request, 'Address added successfully!')
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('profile')
    
    return redirect('profile')


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.label = request.POST.get('label')
        address.address_line = request.POST.get('address_line')
        address.city = request.POST.get('city')
        address.postal_code = request.POST.get('postal_code', '')
        address.phone = request.POST.get('phone')
        address.is_default = request.POST.get('is_default') == 'on'
        address.save()
        
        messages.success(request, 'Address updated successfully!')
        return redirect('profile')
    
    return redirect('profile')


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
    
    return redirect('profile')


@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.is_default = True
        address.save()
        messages.success(request, 'Default address updated!')
    
    return redirect('profile')