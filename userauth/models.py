from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, help_text="e.g., Home, Office, Other")
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.label} - {self.user.username}"

    def save(self, *args, **kwargs):
        # If this is set as default, unset other defaults
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        
        # Check address limit (max 3)
        if not self.pk:  # Only for new addresses
            address_count = Address.objects.filter(user=self.user).count()
            if address_count >= 3:
                raise ValueError("Maximum 3 addresses allowed per user")
        
        # Set as default if it's the first address
        if not self.pk and not Address.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super().save(*args, **kwargs)
