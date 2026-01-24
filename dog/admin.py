from django.contrib import admin
from .models import Dog, DogImage

# Register your models here.

class DogImageInline(admin.TabularInline):
    model = DogImage
    extra = 3
    max_num = 5

@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'gender', 'age', 'behaviour', 'lister', 'location', 'is_approved', 'is_adopted', 'created_at']
    list_filter = ['is_approved', 'is_adopted', 'gender', 'breed', 'location', 'created_at']
    search_fields = ['name', 'breed', 'description', 'behaviour', 'location', 'lister__username']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_approved', 'is_adopted']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DogImageInline]

@admin.register(DogImage)
class DogImageAdmin(admin.ModelAdmin):
    list_display = ['dog', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['dog__name']
