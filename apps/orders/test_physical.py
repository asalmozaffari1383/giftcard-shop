from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.catalog.models import Brand, BundleComponent, Category, Product, ProductVariant, Campaign
from apps.payments.models import PaymentTransaction
from apps.payments.services import initiate_payment, verify_callback, fulfill_reconciliation, record_external_refund
from apps.users.models import Address, LoyaltyEntry, User
from .models import Cart, CartItem, Coupon, Order, ShippingMethod
from .physical import advance_order
from .services import cancel_order, checkout, expire_order


@override_settings(PAYMENT_GATEWAY="mock", SMS_ORDER_TEMPLATE_ID="")
class PhysicalCheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("09123456789", is_verified=True)
        self.category = Category.objects.create(title_fa="دفتر", slug="notebooks")
        self.brand = Brand.objects.create(title_fa="کادن", slug="kaden")
        self.product = Product.objects.create(category=self.category, brand=self.brand, sku="NOTE", title_fa="دفتر اولیه",
                                               slug="notebook", price=100000, discount=10, stock=5)
        self.variant = ProductVariant.objects.create(product=self.product, sku="NOTE-ONE", label="یک دفتر", face_value=1, price_toman=100000)
        self.address = Address.objects.create(user=self.user, recipient_name="خریدار", phone_number=self.user.phone_number,
                                              province="تهران", city="تهران", address="نشانی آزمایشی", postal_code="1234567890")
        self.shipping = ShippingMethod.objects.create(title="پست", price_toman=65000, free_above_toman=200000)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=2)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def order(self, key="physical-order-001", **kwargs):
        return checkout(self.user, idempotency_key=key, address_id=self.address.pk, shipping_method_id=self.shipping.pk, **kwargs)[0]

    def pay(self, order):
        payment, url = initiate_payment(self.user, order.pk, f"payment-{order.pk}")
        query = parse_qs(urlsplit(url).query)
        verify_callback(payment.pk, query["Authority"][0], query["Status"][0])
        order.refresh_from_db()
        return payment

    def test_stock_prices_shipping_and_retry_are_consistent(self):
        catalog = self.client.get("/api/v1/catalog/products/notebook/")
        self.assertEqual(catalog.data["variants"][0]["stock"], 5)
        self.assertEqual(catalog.data["variants"][0]["price_toman"], 90000)
        self.assertEqual(self.client.get("/api/v1/orders/cart/").data[0]["price_toman"], 90000)
        order = self.order()
        again = self.order()
        self.product.refresh_from_db()
        self.assertEqual(order.pk, again.pk)
        self.assertEqual((order.subtotal_toman, order.shipping_toman, order.total_toman), (180000, 65000, 245000))
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(order.stock_reservations.count(), 1)
        self.assertFalse(self.cart.items.exists())

    def test_cancel_restores_stock_and_coupon_once(self):
        Coupon.objects.create(code="SAVE", percent_off=10, usage_limit=10, starts_at=timezone.now() - timedelta(days=1), ends_at=timezone.now() + timedelta(days=1))
        order = self.order(coupon_code="save")
        cancel_order(self.user, order.pk)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(Coupon.objects.get(code="SAVE").used_count, 0)
        with self.assertRaises(ValidationError):
            cancel_order(self.user, order.pk)

    def test_checkout_requires_owned_address(self):
        other = User.objects.create_user("09123456788")
        Address.objects.filter(pk=self.address.pk).update(user=other)
        with self.assertRaises(ValidationError):
            self.order()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(self.cart.items.count(), 1)

    def test_insufficient_stock_is_atomic(self):
        self.product.stock = 1
        self.product.save()
        with self.assertRaises(ValidationError):
            self.order()
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.cart.items.count(), 1)

    def test_payment_shipping_delivery_and_loyalty(self):
        order = self.order()
        payment = self.pay(order)
        self.assertEqual(order.status, Order.Status.PROCESSING)
        self.assertEqual(order.stock_reservations.get().state, "CONSUMED")
        self.assertEqual(LoyaltyEntry.objects.count(), 0)
        with self.assertRaises(ValidationError):
            advance_order(order.pk, Order.Status.SHIPPED)
        advance_order(order.pk, Order.Status.SHIPPED, "POST123456")
        advance_order(order.pk, Order.Status.COMPLETED)
        with self.assertRaises(ValidationError):
            advance_order(order.pk, Order.Status.COMPLETED)
        self.assertEqual(LoyaltyEntry.objects.count(), 1)
        self.assertEqual(LoyaltyEntry.objects.get().points, 24)
        detail = self.client.get(f"/api/v1/orders/{order.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["items"][0]["codes"], [])
        self.assertEqual(detail.data["tracking_code"], "POST123456")
        self.assertEqual(len(detail.data["status_history"]), 4)
        verify_callback(payment.pk, payment.authority, "OK")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_expiry_releases_physical_stock(self):
        order = self.order()
        Order.objects.filter(pk=order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        expire_order(order.pk)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(order.status, Order.Status.FAILED)

    def test_bundle_and_separate_item_share_component_stock(self):
        bundle = Product.objects.create(category=self.category, brand=self.brand, sku="PACK", title_fa="پک", slug="pack",
                                        price=200000, stock=3, is_bundle=True)
        BundleComponent.objects.create(bundle=bundle, product=self.product, quantity=2)
        variant = ProductVariant.objects.create(product=bundle, sku="PACK-ONE", label="پک", face_value=1, price_toman=200000)
        CartItem.objects.create(cart=self.cart, variant=variant, quantity=1)
        self.assertEqual(bundle.available_quantity, 2)
        order = self.order()
        self.product.refresh_from_db()
        bundle.refresh_from_db()
        self.assertEqual((self.product.stock, bundle.stock), (1, 2))
        cancel_order(self.user, order.pk)
        self.product.refresh_from_db()
        bundle.refresh_from_db()
        self.assertEqual((self.product.stock, bundle.stock), (5, 3))

    def test_campaign_and_amount_coupon_do_not_discount_shipping(self):
        now = timezone.now()
        Campaign.objects.create(title="بازگشایی", category=self.category, percent_off=20, starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=1))
        Coupon.objects.create(code="AMOUNT", amount_off=30000, max_discount_toman=10000, starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=1))
        order = self.order(coupon_code="AMOUNT")
        self.assertEqual((order.subtotal_toman, order.discount_toman, order.total_toman), (160000, 10000, 215000))
        catalog = self.client.get("/api/v1/catalog/products/?discounted=true&ordering=effective_price&max_price=85000")
        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(catalog.data["results"][0]["final_price"], 80000)

    def test_free_shipping_uses_subtotal(self):
        self.cart.items.update(quantity=3)
        order = self.order()
        self.assertEqual(order.shipping_toman, 0)
        self.assertEqual(order.total_toman, 270000)

    def test_snapshot_title_survives_catalog_changes(self):
        order = self.order()
        Product.objects.filter(pk=self.product.pk).update(title_fa="نام تازه")
        detail = self.client.get(f"/api/v1/orders/{order.pk}/")
        self.assertEqual(detail.data["items"][0]["product_title"], "دفتر اولیه")

    def test_late_verified_payment_can_be_reconciled_with_intact_stock(self):
        order = self.order()
        payment, _ = initiate_payment(self.user, order.pk, "late-payment-key")
        Order.objects.filter(pk=order.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        result = verify_callback(payment.pk, payment.authority, "OK")
        self.assertEqual(result.status, PaymentTransaction.Status.RECONCILIATION)
        fulfill_reconciliation(payment.pk)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PROCESSING)

    def test_refund_before_shipping_restocks_without_duplicate_charge_refund(self):
        order = self.order()
        payment = self.pay(order)
        operator = User.objects.create_superuser("09123456787", "admin-test-password")
        duplicate = PaymentTransaction.objects.create(order=order, amount_toman=order.total_toman, idempotency_key="duplicate-charge",
                                                       authority="duplicate-authority", status=PaymentTransaction.Status.RECONCILIATION)
        record_external_refund(duplicate.pk, "duplicate-refund", operator)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual((order.status, self.product.stock), (Order.Status.PROCESSING, 3))
        record_external_refund(payment.pk, "original-refund", operator)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual((order.status, self.product.stock), (Order.Status.REFUNDED, 5))
