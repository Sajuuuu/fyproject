from django.contrib import admin
from .models import Product, Size

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category',)
    filter_horizontal = ('sizes',)   # works now!

admin.site.register(Product, ProductAdmin)
admin.site.register(Size)


