from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='home'),
    path('about/', views.about_us, name='about'),
    path('shop/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Admin dashboard and product management
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/data/', views.admin_sales_data, name='admin_sales_data'),
    path('admin/dashboard/export/', views.admin_export_sales_csv, name='admin_export_sales_csv'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # Newsletter subscribe (Join the Glow Club)
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),

    # Account pages
    path('account/orders/', views.account_orders, name='account_orders'),
    path('account/orders/<int:pk>/reorder/', views.reorder, name='reorder'),
    path('account/wishlist/', views.account_wishlist, name='account_wishlist'),

    path('product/add/', views.product_create, name='product_create'),
    path('product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
]


