from django.test import TestCase
from django.urls import reverse

from .models import Brand, Category, Product


class ProductArtworkTests(TestCase):
    def setUp(self):
        category = Category.objects.create(title_fa="گیفت کارت", slug="gift-card")
        brand = Brand.objects.create(title_fa="PlayStation", slug="playstation")
        self.product = Product.objects.create(
            category=category, brand=brand, sku="TEST-ART", title_fa="گیفت کارت پلی استیشن آمریکا",
            slug="playstation-us-gift-card", is_active=True,
        )

    def test_artwork_is_public_svg(self):
        response = self.client.get(reverse("product-artwork", kwargs={"slug": self.product.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertContains(response, "PlayStation")

    def test_product_api_uses_generated_artwork_when_image_is_missing(self):
        response = self.client.get(reverse("product-detail", kwargs={"slug": self.product.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertIn("/artwork/", response.json()["image"])
