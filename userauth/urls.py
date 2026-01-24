from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signin/', views.signinpage, name='signin'),
    path('login/',views.loginpage,name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('profile/', views.profile, name='profile'),
    path('account/update/', views.update_account, name='update_account'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('orders/', views.all_orders, name='all_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('listings/', views.all_listings, name='all_listings'),
]
