from django.contrib import admin
from .models import Address

# Register your models here.

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'city', 'phone', 'is_default', 'created_at']
    list_filter = ['is_default', 'city']
    search_fields = ['user__username', 'label', 'city', 'address_line']
