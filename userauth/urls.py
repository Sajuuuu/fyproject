from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signinpage, name='signin'),
    path('login/',views.loginpage,name='login'),
    path('logout/', views.logout_view, name='logout'),
]
