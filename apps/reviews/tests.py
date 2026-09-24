from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.orders.models import Order, OrderItem
from apps.users.models import User

from .models import Review


class ReviewAPITests(APITestCase):
    def setUp(self):
        self.buyer = User.objects.create_user("09123456789")
        self.other = User.objects.create_user("09123456788")
        category = Category.objects.create(title_fa="کارت هدیه", slug="review-gift")
        brand = Brand.objects.create(title_fa="برند", slug="review-brand")
        self.product = Product.objects.create(category=category, brand=brand, sku="RP1",
                                              title_fa="محصول", slug="review-product")
        variant = ProductVariant.objects.create(product=self.product, sku="RV1", label="10 USD",
                                                face_value=10, price_toman=1000)
        order = Order.objects.create(user=self.buyer, status=Order.Status.COMPLETED,
                                     subtotal_toman=1000, total_toman=1000,
                                     expires_at=timezone.now() + timedelta(minutes=10),
                                     paid_at=timezone.now())
        OrderItem.objects.create(order=order, variant=variant, quantity=1, unit_price_toman=1000)

    def test_verified_buyer_can_review_and_edit_resets_approval(self):
        self.client.force_authenticate(self.buyer)
        created = self.client.post("/api/v1/reviews/", {
            "product": self.product.pk, "rating": 5, "body": "عالی بود",
        })
        self.assertEqual(created.status_code, 201)
        review = Review.objects.get(pk=created.data["id"])
        review.status = Review.Status.APPROVED
        review.save(update_fields=["status"])
        updated = self.client.patch(f"/api/v1/reviews/{review.pk}/", {"body": "نسخه جدید نظر"})
        self.assertEqual(updated.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.status, Review.Status.PENDING)

    def test_non_buyer_cannot_review(self):
        self.client.force_authenticate(self.other)
        response = self.client.post("/api/v1/reviews/", {
            "product": self.product.pk, "rating": 4, "body": "نظر غیرمجاز",
        })
        self.assertEqual(response.status_code, 400)
