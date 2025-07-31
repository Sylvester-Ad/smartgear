from django.db import models
from django.contrib.auth.models import AbstractUser

from smartgear_api import settings

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)


class Product(models.Model):
    name = models.CharField(max_length=250)
    price = models.IntegerField() # in pesewas
    quantity = models.IntegerField(default=1)
    description = models.TextField()
    
    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transactions")
    email = models.EmailField()
    amount = models.IntegerField()
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def total_amount(self):
        total = sum([item.subtotal() for item in self.items.all()])
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity
    
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="pending")
    total_amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order {self.reference} by {self.user.username}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_item")
    quantity = models.PositiveBigIntegerField()
    price_at_purchase = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    

    
    

