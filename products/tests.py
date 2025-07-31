from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Product, Cart, CartItem, Transaction
import json
import hmac
import hashlib
from smartgear_api.settings import PAYSTACK_SECRET_KEY

User = get_user_model()

class CheckoutFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.product = Product.objects.create(name="Test Product", price=10.00)

    def test_user_registration_success(self):
        response = self.client.post(reverse("products:registerview"), {
            "username": "newuser",
            "email": "new@example.com",
            "password": "testpass123"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_missing_fields(self):
        response = self.client.post(reverse("products:registerview"), {"email": "fail@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_item_to_cart(self):
        response = self.client.post(reverse("products:cart-add"), {
            "product_id": self.product.id,
            "quantity": 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_list_cart_items(self):
        CartItem.objects.create(cart=Cart.objects.create(user=self.user), product=self.product, quantity=3)
        response = self.client.get(reverse("products:cart-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_clear_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(reverse("products:cart-clear"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 0)

    def test_initialize_payment_missing_reference(self):
        response = self.client.post(reverse("products:transactions-initialize-payment"), {})
        self.assertEqual(response.status_code, 400)

    def test_paystack_webhook_valid_signature(self):
        payload = json.dumps({
            "event": "charge.success",
            "data": {
                "reference": "ref123",
                "amount": 1000,
                "customer": {"email": self.user.email},
                "status": "success"
            }
        }).encode()

        signature = hmac.new(PAYSTACK_SECRET_KEY.encode(), payload, hashlib.sha512).hexdigest()

        response = self.client.post(
            reverse("products:paystack-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Transaction.objects.filter(reference="ref123", user=self.user).exists())

    def test_paystack_webhook_invalid_signature(self):
        payload = json.dumps({"event": "charge.success", "data": {}}).encode()

        response = self.client.post(
            reverse("products:paystack-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="invalidsignature"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
