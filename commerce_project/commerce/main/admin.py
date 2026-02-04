from django.contrib import admin
from .models import Category, Product, Sale, Order, OrderItem, Wishlist

# Admin Header Styling
admin.site.site_header = "Glow & Care Admin"
admin.site.site_title = "Skincare Portal"
admin.site.index_title = "Welcome to your Beauty Store Management"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Jo fields aap admin list mein dekhna chahte hain
    list_display = ('brand', 'name', 'price', 'cost_price', 'stock', 'skin_type')
    list_filter = ('category', 'skin_type', 'is_vegan')
    search_fields = ('name', 'brand')
    ordering = ('-created_at',) 
    fields = ('name', 'brand', 'category', 'price', 'cost_price', 'stock', 'image', 'skin_type', 'ingredients', 'is_vegan')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'sale_price', 'sold_at', 'order')
    list_filter = ('sold_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__email',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')


admin.site.register(Category)