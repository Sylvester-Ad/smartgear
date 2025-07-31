from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    TransactionViewSet,
    PaystackWebhookView,
    CartViewSet,
    RegisterView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'cart', CartViewSet, basename='cart')

app_name = "products"

urlpatterns = [
    path('', include(router.urls)), 
    path('register/', RegisterView.as_view(), name='registerview'), 
    path('paystack/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),
]
