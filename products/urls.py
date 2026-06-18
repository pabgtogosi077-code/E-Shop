from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('products/<slug:slug>/review/', views.add_review_view, name='add_review'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_view, name='update_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('contact/', views.contact_view, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('support/message/', views.support_message_view, name='support_message'),
    path('api/products/', views.api_products_view, name='api_products'),
    path('api/products/<slug:slug>/', views.api_product_detail_view, name='api_product_detail'),
    path('api/orders/', views.api_orders_view, name='api_orders'),
]
