from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Address
from shop.recommendations import get_trending_products, get_personalized_recommendations
import random
import string

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

def generate_unique_username(first_name, last_name):
    """Generate a unique username from first and last name"""
    base_username = f"{first_name.lower()}{last_name.lower()}"
    # Remove spaces and special characters
    base_username = ''.join(c for c in base_username if c.isalnum())
    
    username = base_username
    counter = 1
    
    # Keep adding numbers until we find a unique username
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def send_verification_email(user, request):
    """Send email verification link to user"""
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build verification URL
    domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    verification_url = f"{protocol}://{domain}/verify-email/{uid}/{token}/"
    
    subject = 'Verify Your Pethood Account'
    message = f"""
    Hi {user.first_name},
    
    Thank you for registering with Pethood!
    
    Please verify your email address by clicking the link below:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    
    Best regards,
    The Pethood Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def signinpage(request):
    error_message = None
   
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        accept_terms = request.POST.get('accept_terms')

        if not accept_terms:
            error_message = "You must accept the Terms of Use and Privacy Policy to create an account."
        elif not first_name or not last_name:
            error_message = "First name and last name are required."
        elif pass1 != pass2:
            error_message = "Your password and confirm password are not the same!"
        elif User.objects.filter(email__iexact=email).exists():
            error_message = "Email already exists!"
        elif len(pass1) < 8:
            error_message = "Password must be at least 8 characters long."
        else:
            # Generate unique username
            username = generate_unique_username(first_name, last_name)
            
            # Create user (inactive until email verified)
            myuser = User.objects.create_user(
                username=username,
                email=email,
                password=pass1,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Inactive until email verified
            )
            myuser.save()
            
            # Send verification email
            email_sent = send_verification_email(myuser, request)
            
            if not email_sent:
                # If email failed, delete the user and show error
                myuser.delete()
                error_message = "Failed to send verification email. Please try again or contact support if the problem persists."
            else:
                messages.success(request, "Account created! Please check your email to verify your account.")
                return redirect('login')

    return render(request, 'signup.html', {'error_message': error_message})

def verify_email(request, uidb64, token):
    """Verify user email address"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Verification link is invalid or has expired.")
        return redirect('home')

def loginpage(request):
    if request.method == "POST":
        username_or_email = request.POST.get("username")
        password = request.POST.get("password")

        # Check if input is email or username
        user_obj = None
        if '@' in username_or_email:
            # Try to find user by email
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                messages.error(request, "Invalid email or password.")
                return redirect("login")
        else:
            username = username_or_email
            try:
                user_obj = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password.")
                return redirect("login")

        # Check if user is verified
        if not user_obj.is_active:
            # Store email in session for resend verification
            request.session['unverified_email'] = user_obj.email
            messages.error(request, "Please verify your email address first. Check your inbox for the verification link.")
            return render(request, 'login.html', {'show_resend': True})

        # Now authenticate with password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

def resend_verification(request):
    """Resend verification email to unverified user"""
    email = request.session.get('unverified_email')
    
    if not email:
        messages.error(request, "No pending verification found. Please try logging in first.")
        return redirect('login')
    
    try:
        user = User.objects.get(email=email, is_active=False)
        
        if send_verification_email(user, request):
            messages.success(request, "Verification email resent! Please check your inbox.")
        else:
            messages.error(request, "Failed to send verification email. Please try again later.")
    except User.DoesNotExist:
        messages.error(request, "User not found or already verified.")
    
    return redirect('login')

def logout_view(request):
    logout(request)  # clears session
    return redirect('home')  # redirect wherever you want


# Profile and Address Management
@login_required
def profile(request):
    from shop.models import Order
    from dog.models import Dog
    
    addresses = Address.objects.filter(user=request.user)
    can_add_more = addresses.count() < 3
    
    # Get user's order history (only 5 recent)
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')[:5]
    total_orders = Order.objects.filter(user=request.user).count()
    
    # Get user's dog listings (only 5 recent)
    my_dogs = Dog.objects.filter(lister=request.user).order_by('-created_at')[:5]
    total_dogs = Dog.objects.filter(lister=request.user).count()
    
    context = {
        'addresses': addresses,
        'can_add_more': can_add_more,
        'orders': orders,
        'my_dogs': my_dogs,
        'total_orders': total_orders,
        'total_dogs': total_dogs,
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

@login_required
def update_account(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        messages.success(request, 'Account information updated successfully!')
        return redirect('profile')
    
    return redirect('profile')

@login_required
def all_orders(request):
    """View all user orders"""
    from shop.models import Order
    
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    
    return render(request, 'all_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """View detailed information about a specific order"""
    from shop.models import Order
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, 'order_detail.html', {'order': order})

@login_required
def all_listings(request):
    """View all user's dog listings"""
    from dog.models import Dog
    
    my_dogs = Dog.objects.filter(lister=request.user).order_by('-created_at')
    
    return render(request, 'all_listings.html', {'my_dogs': my_dogs})