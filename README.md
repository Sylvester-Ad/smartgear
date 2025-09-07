# SmartGear Checkout Backend API

A Django REST Framework backend for a SmartPay Checkout system. This API handles user authentication, product listing, cart management, Paystack payment integration, and webhook handling.

---

## 🚀 Features

* JWT Authentication (Login, Register, Refresh)
* Product listing (Read-only)
* Cart management (Add, View, Clear)
* Paystack payment initialization
* Webhook handler for payment verification
* Swagger and Redoc API documentation

---

## 📦 Requirements

* Python 3.10+
* Django 4.x
* Django REST Framework
* drf-yasg (for Swagger docs)
* djangorestframework-simplejwt
* requests

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Setup

Create a `.env` file and set the following values:

```env
PAYSTACK_SECRET_KEY=your_paystack_secret_key
DJANGO_SECRET_KEY=your_django_secret_key
```

And in your `settings.py`, load them like:

```python
import os

PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
```

This ensures secrets are not hardcoded and can be injected securely during deployment.

---

## 🔐 Authentication Endpoints

| Endpoint          | Method | Description                   |
| ----------------- | ------ | ----------------------------- |
| `/auth/register/` | POST   | Register a new user           |
| `/auth/login/`    | POST   | Get access and refresh tokens |
| `/auth/refresh/`  | POST   | Refresh access token          |

---

## 🛒 API Endpoints

| Endpoint                                | Method | Description              |
| --------------------------------------- | ------ | ------------------------ |
| `/api/products/`                        | GET    | List all products        |
| `/api/cart/`                            | GET    | View cart items          |
| `/api/cart/add/`                        | POST   | Add item to cart         |
| `/api/cart/clear/`                      | POST   | Clear all cart items     |
| `/api/transactions/`                    | GET    | List user transactions   |
| `/api/transactions/initialize-payment/` | POST   | Start Paystack payment   |
| `/api/paystack/webhook/`                | POST   | Paystack webhook handler |

---

## 📘 API Docs

* Swagger UI: [http://localhost:8000/swagger/](http://localhost:8000/swagger/)
* Redoc UI: [http://localhost:8000/redoc/](http://localhost:8000/redoc/)

Authorize with your JWT token by clicking the **"Authorize"** button and pasting:

```
Bearer your_access_token
```

---

## 🧪 Running Tests

```bash
python manage.py test
```

Covers:

* Registration
* Login
* Cart operations
* Payment initialization
* Webhook verification

---

## 🚀 Deployment Notes

1. Set `DEBUG = False` in `settings.py`
2. Add allowed hosts:

```python
ALLOWED_HOSTS = ["yourdomain.com"]
```

3. Set up Gunicorn, nginx, PostgreSQL (or your preferred DB)
4. Use `python manage.py collectstatic` if serving static files
5. Make sure `.env` is securely configured and loaded
6. Set `DJANGO_SECRET_KEY` as an environment variable in your hosting platform

---

## 🧑🏽‍💻 Contributors

* Backend: Sylvester-Ad, Roma
* Frontend: \[Frontend Dev Team]

---

## 📬 Questions or Bugs?

Open an issue or contact: [devteam@smartpay.com](mailto:devteam@smartpay.com)
