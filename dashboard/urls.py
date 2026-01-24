from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Home
    path('', views.dashboard_home, name='home'),
    
    # Product Management
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Dog Management
    path('dogs/', views.dog_list, name='dog_list'),
    path('dogs/<int:dog_id>/approve/', views.dog_approve, name='dog_approve'),
    path('dogs/<int:dog_id>/reject/', views.dog_reject, name='dog_reject'),
    path('dogs/<int:dog_id>/adopt/', views.dog_mark_adopted, name='dog_mark_adopted'),
    
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    
    # Order Management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
]
