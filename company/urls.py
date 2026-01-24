from django.urls import path
from . import views

urlpatterns = [
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    path('about-us/', views.about_us, name='about_us'),
]
