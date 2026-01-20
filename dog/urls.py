from django.urls import path
from . import views

app_name = 'dog'

urlpatterns = [
    path('', views.dog_list, name='dog_list'),
    path('<slug:slug>/', views.dog_detail, name='dog_detail'),
]