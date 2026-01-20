from django.shortcuts import render, get_object_or_404
from .models import Dog

# Create your views here.

def dog_list(request):
    """Display all dogs available for adoption"""
    dogs = Dog.objects.filter(is_adopted=False)
    context = {
        'dogs': dogs,
        'total_dogs': dogs.count()
    }
    return render(request, 'dog_list.html', context)

def dog_detail(request, slug):
    """Display detailed information about a specific dog"""
    dog = get_object_or_404(Dog, slug=slug)
    context = {
        'dog': dog
    }
    return render(request, 'dog_detail.html', context)
