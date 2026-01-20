from django.db import models
from django.utils.text import slugify

# Create your models here.

class Dog(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    breed = models.CharField(max_length=100)
    age = models.CharField(max_length=50)  # e.g., "2 years", "6 months"
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Adoption fee")
    description = models.TextField()
    story = models.TextField(help_text="The dog's background story")
    image = models.ImageField(upload_to='dogs/', blank=True, null=True)
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

    def __str__(self):
        return f"{self.name} - {self.breed}"

    class Meta:
        ordering = ['-created_at']
