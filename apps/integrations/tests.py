import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Product, ProductVariant

from .catalog import CandidateData, normalize_title, parse_uploaded_catalog, publish_candidate, upsert_candidates
from .models import CatalogCandidate, CatalogSource


class CatalogImportTests(TestCase):
    def setUp(self):
        self.source = CatalogSource.objects.create(
            name="منبع آزمایشی", slug="test-source", base_url="https://example.com",
            kind=CatalogSource.Kind.CURATED,
        )

    def test_upsert_is_idempotent(self):
        candidate = CandidateData(
            external_id="gift-card-10", source_url="https://example.com/gift-card-10",
            title="گیفت کارت ۱۰ دلاری اپل", source_price=500_000, source_currency="IRT",
        )

        first = upsert_candidates(self.source, [candidate])
        second = upsert_candidates(self.source, [candidate])

        self.assertEqual(first, (1, 1, 0))
        self.assertEqual(second, (1, 0, 1))
        self.assertEqual(CatalogCandidate.objects.count(), 1)

    def test_json_upload_parser(self):
        payload = {"products": [{
            "external_id": "steam-20", "title": "گیفت کارت استیم ۲۰ دلار",
            "source_url": "https://example.com/steam-20", "price": 900_000,
        }]}
        uploaded = SimpleUploadedFile("products.json", json.dumps(payload).encode())

        products = list(parse_uploaded_catalog(uploaded, uploaded.name))

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].external_id, "steam-20")
        self.assertEqual(products[0].source_price, 900_000)

    def test_publish_creates_disabled_product_and_variant(self):
        candidate = CatalogCandidate.objects.create(
            source=self.source, external_id="apple-10", source_url="https://example.com/apple-10",
            title="گیفت کارت اپل ۱۰ دلار", normalized_title=normalize_title("گیفت کارت اپل ۱۰ دلار"),
            source_price=650_000, source_currency="IRT",
            review_status=CatalogCandidate.ReviewStatus.APPROVED,
            last_seen_at=timezone.now(),
        )

        product = publish_candidate(candidate)

        product.refresh_from_db()
        candidate.refresh_from_db()
        variant = ProductVariant.objects.get(product=product)
        self.assertFalse(product.is_active)
        self.assertFalse(variant.is_active)
        self.assertEqual(candidate.review_status, CatalogCandidate.ReviewStatus.IMPORTED)
        self.assertEqual(candidate.matched_product, product)
        self.assertEqual(Product.objects.count(), 1)

    def test_publish_reuses_product_for_normalized_duplicate(self):
        other_source = CatalogSource.objects.create(
            name="منبع دوم", slug="second-source", base_url="https://second.example.com",
            kind=CatalogSource.Kind.CURATED,
        )
        first = CatalogCandidate.objects.create(
            source=self.source, external_id="apple", source_url="https://example.com/apple",
            title="گیفت کارت اپل", normalized_title=normalize_title("گیفت کارت اپل"),
            review_status=CatalogCandidate.ReviewStatus.APPROVED, last_seen_at=timezone.now(),
        )
        second = CatalogCandidate.objects.create(
            source=other_source, external_id="apple", source_url="https://second.example.com/apple",
            title="گيفت کارت اپل", normalized_title=normalize_title("گيفت کارت اپل"),
            review_status=CatalogCandidate.ReviewStatus.APPROVED, last_seen_at=timezone.now(),
        )

        first_product = publish_candidate(first)
        second_product = publish_candidate(second)

        self.assertEqual(first_product, second_product)
        self.assertEqual(Product.objects.count(), 1)

    def test_normalize_title_unifies_arabic_characters(self):
        self.assertEqual(normalize_title("  گيفت‌کارت APPLE  "), "گیفت کارت apple")

    def test_manual_candidate_fields_are_generated(self):
        candidate = CatalogCandidate.objects.create(
            source=self.source, external_id="manual", source_url="https://example.com/manual",
            title="گيفت کارت دستی",
        )

        self.assertEqual(candidate.normalized_title, "گیفت کارت دستی")
        self.assertIsNotNone(candidate.last_seen_at)

    def test_publish_ignores_invalid_equal_old_price(self):
        candidate = CatalogCandidate.objects.create(
            source=self.source, external_id="equal-price", source_url="https://example.com/equal-price",
            title="گیفت کارت تست", source_price=500_000, source_old_price=500_000,
            source_currency="IRT",
        )

        product = publish_candidate(candidate, activate=True)
        variant = ProductVariant.objects.get(product=product)

        self.assertTrue(product.is_active)
        self.assertTrue(variant.is_active)
        self.assertIsNone(variant.old_price_toman)
        self.assertEqual(variant.digital_items.count(), 0)
