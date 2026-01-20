from django.contrib import admin
from .models import Dog

# Register your models here.

@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'age', 'price', 'is_adopted', 'created_at']
    list_filter = ['is_adopted', 'breed', 'created_at']
    search_fields = ['name', 'breed', 'description', 'story']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_adopted']
    readonly_fields = ['created_at', 'updated_at']
