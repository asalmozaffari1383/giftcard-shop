from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase

from apps.users.models import User
from .models import Brand, Category, Product


class StationeryAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("09123456789", "admin-test-password")
        self.category = Category.objects.create(title_fa="دفتر", slug="notebook")
        self.brand = Brand.objects.create(title_fa="کادن", slug="kaden")
        self.product = Product.objects.create(category=self.category, brand=self.brand, sku="NOTE", title_fa="دفتر", slug="note", price=100000, stock=5)
        self.model_admin = admin.site._registry[Product]
        self.request = RequestFactory().post("/admin/catalog/product/", {"action": "bulk_update", "select_across": "0", "bulk_price": "150000", "bulk_stock": "10", "bulk_discount": "20"})
        self.request.user = self.user
        self.request.session = {}
        self.request._messages = FallbackStorage(self.request)

    def test_bulk_update_works_with_annotated_admin_queryset(self):
        self.model_admin.bulk_update(self.request, self.model_admin.get_queryset(self.request))
        self.product.refresh_from_db()
        self.assertEqual((self.product.price, self.product.stock, self.product.discount), (150000, 10, 20))

    def test_new_physical_product_gets_a_purchasable_variant(self):
        self.model_admin.save_related(self.request, SimpleNamespace(instance=self.product, save_m2m=Mock()), [], False)
        variant = self.product.variants.get()
        self.assertEqual(variant.price_toman, 100000)
        self.assertEqual(variant.currency, "IRT")

    def test_sales_dashboard_requires_admin_login(self):
        self.assertEqual(self.client.get("/admin/overview/").status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get("/admin/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "هشدار موجودی کم")
