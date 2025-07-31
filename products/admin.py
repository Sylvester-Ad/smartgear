from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Product, 
    Transaction, 
    CustomUser, 
    CartItem, 
    Cart,
    Order, 
    OrderItem
)

admin.site.register(Product)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Transaction)
admin.site.register(CartItem)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
