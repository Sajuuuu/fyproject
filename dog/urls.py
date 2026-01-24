from django.urls import path
from . import views

app_name = 'dog'

urlpatterns = [
    path('', views.dog_list, name='dog_list'),
    path('add/', views.add_dog_listing, name='add_dog_listing'),
    path('<slug:slug>/', views.dog_detail, name='dog_detail'),
]