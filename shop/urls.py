from django.urls import path
from . import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('shop', views.shop_home, name='shop_home'),
    path('<int:pk>/', views.productdetails, name='productdetails'),
    #  path('collections_view', views.collections_view, name='collections_view'),
    path('cart/', views.cart_view, name='cart_view'),  # <- This must match redirect
    path('add-to-cart-ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('update-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)