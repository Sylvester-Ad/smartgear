import hashlib
import hmac
import json
import requests
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from smartgear_api import settings
from smartgear_api.settings import PAYSTACK_SECRET_KEY
from .models import Product, Transaction, Cart, CartItem, Order, OrderItem
from .serializers import ProductSerializer, TransactionSerializer, RegisterSerializer, CartItemSerializer

User = get_user_model()

# ------------------------
# User Registration View
# ------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------
# Product Read-Only View
# ------------------------
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = [IsAuthenticated] 
    # Only authenticated users can view products


# ------------------------
# Cart Management ViewSet
# ------------------------
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # List all cart items for the current user
    def list(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(cart.items.all(), many=True)
        return Response(serializer.data)

    # Add a product to the cart (or increase quantity if it already exists)
    @action(detail=False, methods=['post'])
    def add(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        if not product_id:
            return Response({'error': 'Product ID is required'}, status=400)

        try:
            product = Product.objects.get(id=product_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)
            item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                item.quantity += quantity
            else:
                item.quantity = quantity
            item.save()
            return Response({'message': 'Item added to cart'})
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

    # Clear all items in the cart
    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'})


# -----------------------------
# Transaction & Payment Views
# -----------------------------
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    # Filter transactions to only return the current user's
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    # Custom route to initialize Paystack payment
    @action(detail=False, methods=['post'], url_path='initialize-payment')
    def initialize_payment(self, request):
        user = request.user
        email = user.email
        reference = request.data.get('reference')

        # Compute total cart amount in minor currency (e.g. pesewas or kobo)
        cart, _ = Cart.objects.get_or_create(user=user)
        amount = int(sum([item.product.price * item.quantity for item in cart.items.all()]) * 100)

        if not reference:
            return Response({"error": "Reference is required"}, status=400)

        headers = {
            'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        data = {
            'email': email,
            'amount': amount,
            'reference': reference,
        }

        # Call Paystack API to initialize payment
        try:
            res = requests.post('https://api.paystack.co/transaction/initialize', json=data, headers=headers)
            res.raise_for_status()
        except requests.RequestException as e:
            return Response({'error': 'Payment initialization failed', 'details': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        if res.status_code == 200:
            response_data = res.json().get('data', {})

            # Save transaction in database as pending
            Transaction.objects.create(
                user=user,
                reference=reference,
                amount=amount,
                status='pending'
            )
            return Response({'auth_url': response_data.get('authorization_url')})

        return Response({'error': 'Payment initialization failed'}, status=res.status_code)


# ------------------------
# Paystack Webhook Handler
# ------------------------
@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Verify signature to ensure request came from Paystack
            secret = PAYSTACK_SECRET_KEY.encode()
            signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE', '')
            payload = request.body
            expected_sig = hmac.new(secret, payload, hashlib.sha512).hexdigest()

            # Simulate signature test comparison for validation
            if signature != expected_sig:
                print("Invalid Paystack signature received")
                return Response({'error': 'Invalid signature'}, status=400)

            # Decode JSON payload
            data = json.loads(payload)
            event = data.get('event')
            event_data = data.get('data', {})

            # Only handle successful payments
            if event == 'charge.success' and event_data.get('status') == 'success':
                reference = event_data.get('reference')
                amount = event_data.get('amount')
                email = event_data.get('customer', {}).get('email')

                try:
                    user = User.objects.get(email=email)

                    # Either create or update the transaction record
                    transaction, created = Transaction.objects.get_or_create(
                        reference=reference,
                        defaults={
                            'user': user,
                            'amount': amount,
                            'status': 'success',
                        }
                    )
                    if not created:
                        transaction.status = 'success'
                        transaction.save()
                    
                    # 

                    # Clear the user's cart, after successful payment
                        try:
                            cart = Cart.objects.get(user=user)
                            
                            # Create the order
                            order = Order.objects.create(
                                user=user,
                                reference=reference,
                                status="success",
                                total_amount=amount,
                            )
                            
                            # Create OderItems from Cart
                            cart_items = CartItem.objects.filter(user=user)
                            for item in cart_items:
                                OrderItem.objects.create(
                                    order=order,
                                    product=item.product,
                                    quantity=item.quantity,
                                    price_at_purchase=item.product.price
                                )
                            # Clear cart
                            cart_items.delete()
                        except Cart.DoesNotExist:
                            pass

                except User.DoesNotExist:
                    print(f"User with email {email} not found")

        except Exception as e:
            print("Webhook error:", e)

        # Always return 200 so Paystack knows the webhook was received
        return Response(status=status.HTTP_200_OK)
