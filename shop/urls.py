from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('shop', views.shop_home, name='shop_home'),
    path('search/', views.search, name='search'),
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('add-to-cart-ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('buy-now-ajax/<int:product_id>/', views.buy_now_ajax, name='buy_now_ajax'),
    path('update-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('khalti-callback/', views.khalti_callback, name='khalti_callback'),
    path('khalti-verify/', views.khalti_verify, name='khalti_verify'),
    path('order-success/', views.order_success, name='order_success'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('<slug:slug>/', views.productdetails, name='productdetails'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)