from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

# Create your models here.

class Dog(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    breed = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    age = models.IntegerField(help_text="Age in months")
    behaviour = models.CharField(max_length=200, help_text="e.g., Friendly, Energetic, Calm, Playful")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Adoption fee", default=0)
    image = models.ImageField(upload_to='dogs/', blank=True, null=True)
    
    # Marketplace fields
    lister = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listed_dogs', null=True, blank=True)
    location = models.CharField(max_length=100, help_text="City or area", blank=True)
    is_approved = models.BooleanField(default=False, help_text="Admin approval status")
    is_adopted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Dog.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def get_age_display(self):
        """Convert months to human-readable format"""
        try:
            age_int = int(self.age) if isinstance(self.age, str) else self.age
        except (ValueError, TypeError):
            return str(self.age)  # Return as-is if conversion fails
        
        if age_int < 12:
            return f"{age_int} month{'s' if age_int != 1 else ''}"
        else:
            years = age_int // 12
            months = age_int % 12
            if months == 0:
                return f"{years} year{'s' if years != 1 else ''}"
            else:
                return f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"

    def __str__(self):
        return f"{self.name} - {self.breed}"

    class Meta:
        ordering = ['-created_at']


class DogImage(models.Model):
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='dogs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Image for {self.dog.name}"
