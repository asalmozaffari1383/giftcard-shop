from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.inventory.models import DigitalItem
from apps.payments.gateways import Verification
from apps.payments.models import PaymentTransaction
from apps.payments.services import (
    fail_stale_payment,
    fulfill_reconciliation,
    initiate_payment,
    record_external_refund,
    verify_callback,
)
from apps.users.models import User

from .models import Cart, CartItem, Order
from .services import checkout, expire_order


@override_settings(ZARINPAL_MERCHANT_ID="test-merchant")
class CheckoutAndFulfillmentTests(TestCase):
    """Run against PostgreSQL; SQLite does not provide row-level locks."""

    def setUp(self):
        self.user = User.objects.create_user("09123456789")
        category = Category.objects.create(title_fa="کارت هدیه", slug="gift")
        brand = Brand.objects.create(title_fa="نمونه", slug="example")
        product = Product.objects.create(category=category, brand=brand, sku="P1", title_fa="کارت نمونه", slug="sample")
        self.variant = ProductVariant.objects.create(product=product, sku="V1", label="10 USD",
                                                     face_value=10, region="US", price_toman=100000)
        for secret in ("secret-one", "secret-two"):
            code = DigitalItem(variant=self.variant)
            code.set_secret(secret)
            code.save()
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)

    def test_checkout_reserves_and_expiration_releases_exact_stock(self):
        order, created = checkout(self.user, idempotency_key="checkout-key-001")
        self.assertTrue(created)
        self.assertEqual(order.total_toman, 200000)
        self.assertEqual(DigitalItem.objects.filter(status=DigitalItem.Status.RESERVED, reserved_order=order).count(), 2)
        CartItem.objects.create(cart=self.user.cart, variant=self.variant, quantity=1)
        with self.assertRaises(ValidationError):
            checkout(self.user, idempotency_key="checkout-key-002")
        Order.objects.filter(pk=order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        expire_order(order.pk)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.FAILED)
        self.assertEqual(DigitalItem.objects.filter(status=DigitalItem.Status.AVAILABLE).count(), 2)

    def test_another_payment_attempt_is_blocked_while_ready(self):
        order, _ = checkout(self.user, idempotency_key="checkout-key-003")
        PaymentTransaction.objects.create(order=order, idempotency_key="first-key-123",
                                          amount_toman=order.total_toman, authority="authority-3",
                                          status=PaymentTransaction.Status.READY)
        with self.assertRaises(ValidationError):
            initiate_payment(self.user, order.pk, "second-key-456")

    def test_stale_initiating_payment_is_failed(self):
        order, _ = checkout(self.user, idempotency_key="checkout-key-008")
        payment = PaymentTransaction.objects.create(order=order, idempotency_key="stale-key-123",
                                                     amount_toman=order.total_toman)
        stale_before = timezone.now() - timedelta(minutes=5)
        PaymentTransaction.objects.filter(pk=payment.pk).update(created_at=stale_before - timedelta(seconds=1))
        self.assertTrue(fail_stale_payment(payment.pk, stale_before))
        payment.refresh_from_db()
        self.assertEqual(payment.status, PaymentTransaction.Status.FAILED)

    @patch("apps.payments.services.ZarinpalGateway.verify", return_value=Verification(True, 100, "ref-1"))
    def test_verified_callback_dispatches_once(self, verify):
        order, _ = checkout(self.user, idempotency_key="checkout-key-004")
        payment = PaymentTransaction.objects.create(order=order, idempotency_key="customer-key-123",
                                                    amount_toman=order.total_toman, authority="authority-1",
                                                    status=PaymentTransaction.Status.READY)
        verify_callback(payment.pk, "authority-1", "OK")
        verify_callback(payment.pk, "authority-1", "OK")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(DigitalItem.objects.filter(status=DigitalItem.Status.SOLD,
                                                    sold_order_item__order=order).count(), 2)
        self.assertEqual(verify.call_count, 1)
        client = APIClient()
        client.force_authenticate(self.user)
        list_response = client.get("/api/v1/orders/")
        detail_response = client.get(f"/api/v1/orders/{order.pk}/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["results"][0]["items"][0]["codes"], [])
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(set(detail_response.data["items"][0]["codes"]), {"secret-one", "secret-two"})
        self.assertEqual(detail_response["Cache-Control"], "no-store")
        payment_response = client.get(f"/api/v1/payments/{payment.pk}/")
        self.assertEqual(payment_response.status_code, 200)
        self.assertEqual(payment_response["Cache-Control"], "no-store")
        other = User.objects.create_user("09123456786")
        client.force_authenticate(other)
        self.assertEqual(client.get(f"/api/v1/payments/{payment.pk}/").status_code, 404)

    @patch("apps.payments.services.ZarinpalGateway.verify", return_value=Verification(True, 100, "ref-2"))
    def test_late_payment_requires_reconciliation(self, verify):
        order, _ = checkout(self.user, idempotency_key="checkout-key-005")
        payment = PaymentTransaction.objects.create(order=order, idempotency_key="customer-key-456",
                                                    amount_toman=order.total_toman, authority="authority-2",
                                                    status=PaymentTransaction.Status.READY)
        Order.objects.filter(pk=order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        result = verify_callback(payment.pk, "authority-2", "OK")
        self.assertEqual(result.status, PaymentTransaction.Status.RECONCILIATION)
        self.assertFalse(DigitalItem.objects.filter(status=DigitalItem.Status.SOLD).exists())
        fulfill_reconciliation(payment.pk)
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(payment.status, PaymentTransaction.Status.VERIFIED)
        self.assertEqual(DigitalItem.objects.filter(status=DigitalItem.Status.SOLD).count(), 2)

    @patch("apps.payments.services.ZarinpalGateway.verify", return_value=Verification(True, 100, "ref-3"))
    def test_refunding_duplicate_charge_keeps_fulfilled_order_completed(self, verify):
        order, _ = checkout(self.user, idempotency_key="checkout-key-006")
        paid = PaymentTransaction.objects.create(order=order, idempotency_key="first-paid-key",
                                                 amount_toman=order.total_toman, authority="authority-paid",
                                                 status=PaymentTransaction.Status.READY)
        verify_callback(paid.pk, "authority-paid", "OK")
        duplicate = PaymentTransaction.objects.create(order=order, idempotency_key="duplicate-key",
                                                      amount_toman=order.total_toman, authority="authority-duplicate",
                                                      reference_id="duplicate-ref",
                                                      status=PaymentTransaction.Status.RECONCILIATION)
        admin = User.objects.create_superuser("09123456788", "strong-secret-password")
        record_external_refund(duplicate.pk, "refund-duplicate", admin)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        record_external_refund(paid.pk, "refund-original", admin)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.REFUNDED)

    def test_checkout_retry_returns_same_order_without_reserving_twice(self):
        first, first_created = checkout(self.user, idempotency_key="checkout-key-007")
        second, second_created = checkout(self.user, idempotency_key="checkout-key-007")
        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(DigitalItem.objects.filter(reserved_order=first).count(), 2)
