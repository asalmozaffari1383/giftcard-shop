from cryptography.fernet import Fernet
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase, override_settings

from apps.catalog.models import Brand, Category, Product, ProductVariant

from .models import DigitalItem


class EncryptedItemTests(SimpleTestCase):
    def test_round_trip_and_key_rotation(self):
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        item = DigitalItem()
        with override_settings(INVENTORY_FERNET_KEYS=[old_key]):
            item.set_secret("Gift-Card-123")
        self.assertNotIn(b"Gift-Card-123", bytes(item.encrypted_payload))
        self.assertEqual(len(item.fingerprint), 64)
        with override_settings(INVENTORY_FERNET_KEYS=[new_key, old_key]):
            self.assertEqual(item.reveal_secret(), "Gift-Card-123")

    def test_equal_secrets_have_equal_fingerprints(self):
        first = DigitalItem()
        second = DigitalItem()
        first.set_secret("same-secret")
        second.set_secret("same-secret")
        self.assertEqual(first.fingerprint, second.fingerprint)


class DuplicateInventoryTests(TestCase):
    def test_duplicate_plaintext_cannot_be_saved_twice(self):
        category = Category.objects.create(title_fa="کارت", slug="duplicate-category")
        brand = Brand.objects.create(title_fa="برند", slug="duplicate-brand")
        product = Product.objects.create(category=category, brand=brand, sku="DP1",
                                         title_fa="محصول", slug="duplicate-product")
        variant = ProductVariant.objects.create(product=product, sku="DV1", label="10",
                                                face_value=10, price_toman=1000)
        first = DigitalItem(variant=variant)
        first.set_secret("duplicate-secret")
        first.save()
        second = DigitalItem(variant=variant)
        second.set_secret("duplicate-secret")
        with self.assertRaises(IntegrityError):
            second.save()
