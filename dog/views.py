from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Dog, DogImage
from .forms import DogListingForm, DogImageForm
from .emails import send_new_listing_to_admin
from userauth.models import Address

# Create your views here.

def dog_list(request):
    """Display all approved dogs available for adoption with filters"""
    dogs = Dog.objects.filter(is_adopted=False, is_approved=True)
    
    # Get filter parameters
    gender = request.GET.get('gender', '')
    age_sort = request.GET.get('age_sort', '')
    breed = request.GET.get('breed', '')
    location = request.GET.get('location', '')
    
    # Apply filters
    if gender:
        dogs = dogs.filter(gender=gender)
    
    if breed:
        dogs = dogs.filter(breed__icontains=breed)
    
    if location:
        dogs = dogs.filter(location__icontains=location)
    
    # Apply age sorting
    if age_sort == 'young':
        dogs = dogs.order_by('age')
    elif age_sort == 'old':
        dogs = dogs.order_by('-age')
    else:
        dogs = dogs.order_by('-created_at')  # Default: newest first
    
    # Get unique breeds and locations for filter dropdowns
    all_breeds = Dog.objects.filter(is_approved=True).values_list('breed', flat=True).distinct()
    all_locations = Dog.objects.filter(is_approved=True).exclude(location='').values_list('location', flat=True).distinct()
    
    context = {
        'dogs': dogs,
        'total_dogs': dogs.count(),
        'selected_gender': gender,
        'selected_age_sort': age_sort,
        'selected_breed': breed,
        'selected_location': location,
        'all_breeds': sorted(set(all_breeds)),
        'all_locations': sorted(set(all_locations)),
        'gender_choices': Dog.GENDER_CHOICES,
    }
    return render(request, 'dog_list.html', context)

@login_required
def dog_detail(request, slug):
    """Display detailed information about a specific dog (login required)"""
    # Staff members can view unapproved dogs, regular users can only view approved ones
    if request.user.is_staff:
        dog = get_object_or_404(Dog, slug=slug)
    else:
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

@login_required
def my_listings(request):
    """Display user's dog listings"""
    my_dogs = Dog.objects.filter(lister=request.user).order_by('-created_at')
    return render(request, 'my_listings.html', {'my_dogs': my_dogs})

@login_required
def edit_dog_listing(request, slug):
    """Edit an existing dog listing"""
    dog = get_object_or_404(Dog, slug=slug, lister=request.user)
    
    if request.method == 'POST':
        form = DogListingForm(request.POST, request.FILES, instance=dog)
        images = request.FILES.getlist('additional_images')
        
        if form.is_valid():
            dog = form.save()
            
            # Add new additional images
            current_images_count = dog.images.count()
            for image in images[:5 - current_images_count]:  # Max 5 total images
                DogImage.objects.create(dog=dog, image=image)
            
            messages.success(request, f'Listing for {dog.name} has been updated successfully!')
            return redirect('profile')
        else:
            # Show specific validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label or field
                        messages.error(request, f'{field_label}: {error}')
    else:
        form = DogListingForm(instance=dog)
    
    return render(request, 'edit_dog_listing.html', {'form': form, 'dog': dog})

@login_required
def delete_dog_listing(request, slug):
    """Delete a dog listing"""
    dog = get_object_or_404(Dog, slug=slug, lister=request.user)
    
    if request.method == 'POST':
        dog_name = dog.name
        dog.delete()
        messages.success(request, f'Listing for {dog_name} has been deleted.')
        return redirect('profile')
    
    return render(request, 'confirm_delete_dog.html', {'dog': dog})

@login_required
def mark_as_adopted(request, slug):
    """Mark a dog as adopted"""
    dog = get_object_or_404(Dog, slug=slug, lister=request.user)
    
    if request.method == 'POST':
        dog.is_adopted = True
        dog.save()
        messages.success(request, f'{dog.name} has been marked as adopted!')
        return redirect('profile')
    
    return redirect('profile')
