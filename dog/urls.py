from django.urls import path
from . import views

app_name = 'dog'

urlpatterns = [
    path('', views.dog_list, name='dog_list'),
    path('add/', views.add_dog_listing, name='add_dog_listing'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('edit/<slug:slug>/', views.edit_dog_listing, name='edit_dog_listing'),
    path('delete/<slug:slug>/', views.delete_dog_listing, name='delete_dog_listing'),
    path('mark-adopted/<slug:slug>/', views.mark_as_adopted, name='mark_as_adopted'),
    path('<slug:slug>/', views.dog_detail, name='dog_detail'),
]