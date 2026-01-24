from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Dog, DogImage
from .forms import DogListingForm, DogImageForm
from .emails import send_new_listing_to_admin
from userauth.models import Address

# Create your views here.

def dog_list(request):
    """Display all approved dogs available for adoption (no login required)"""
    dogs = Dog.objects.filter(is_adopted=False, is_approved=True)
    context = {
        'dogs': dogs,
        'total_dogs': dogs.count()
    }
    return render(request, 'dog_list.html', context)

@login_required
def dog_detail(request, slug):
    """Display detailed information about a specific dog (login required)"""
    dog = get_object_or_404(Dog, slug=slug, is_approved=True)
    
    # Get lister's default address for phone number
    lister_phone = None
    if dog.lister:
        default_address = Address.objects.filter(user=dog.lister, is_default=True).first()
        if default_address:
            lister_phone = default_address.phone
    
    context = {
        'dog': dog,
        'lister_phone': lister_phone
    }
    return render(request, 'dog_detail.html', context)

@login_required
def add_dog_listing(request):
    """Allow users to submit a dog for adoption"""
    # Check if user has a default address with phone number
    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    
    if not default_address:
        messages.warning(request, 'Please add a default address with your phone number before listing a dog for adoption.')
        return redirect('profile')
    
    if not default_address.phone:
        messages.warning(request, 'Please add a phone number to your default address before listing a dog for adoption.')
        return redirect('profile')
    
    if request.method == 'POST':
        form = DogListingForm(request.POST, request.FILES)
        
        # Get additional images
        images = request.FILES.getlist('additional_images')
        
        if form.is_valid():
            dog = form.save(commit=False)
            dog.lister = request.user
            dog.is_approved = False  # Needs admin approval
            dog.save()
            
            # Save additional images
            for image in images[:4]:  # Max 4 additional images
                DogImage.objects.create(dog=dog, image=image)
            
            # Send notification to admin
            send_new_listing_to_admin(dog)
            
            messages.success(request, f'Your listing for {dog.name} has been submitted! It will be visible once approved by admin.')
            return redirect('dog:dog_list')
    else:
        form = DogListingForm()
    
    return render(request, 'add_dog_listing.html', {'form': form})
