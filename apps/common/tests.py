from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APITestCase
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import HttpResponse
from apps.common.middleware import CatalogOnlyMiddleware
from apps.common.management.commands.production_check import collect_production_issues


@override_settings(CATALOG_ONLY=True)
class CatalogOnlyTests(SimpleTestCase):
    def setUp(self):
        self.middleware = CatalogOnlyMiddleware(lambda request: HttpResponse("allowed"))
        self.factory = RequestFactory()

    def test_catalog_admin_and_health_remain_accessible(self):
        for path in ("/api/v1/catalog/products/", "/admin/", "/health/ready/"):
            self.assertEqual(self.middleware(self.factory.get(path)).status_code, 200)

    def test_customer_writes_and_payment_callbacks_are_disabled(self):
        for path in ("/api/v1/auth/otp/request/", "/api/v1/auth/otp/verify/",
                     "/api/v1/orders/checkout/", "/api/v1/payments/initiate/",
                     "/api/v1/catalog/products/"):
            self.assertEqual(self.middleware(self.factory.post(path)).status_code, 503)
        self.assertEqual(self.middleware(self.factory.get("/api/v1/payments/callback/123/")).status_code, 503)

    @override_settings(CATALOG_ONLY=False)
    def test_normal_mode_does_not_intercept_requests(self):
        self.assertEqual(self.middleware(self.factory.post("/api/v1/auth/otp/request/")).status_code, 200)

    def test_catalog_mode_still_rejects_insecure_production_and_live_sales(self):
        errors, _ = collect_production_issues(live=True)
        self.assertIn("DEBUG must be false.", errors)
        self.assertIn("CATALOG_ONLY must be false for a live sales launch.", errors)
        self.assertFalse(any("SMS_API_KEY" in error or "ZARINPAL_MERCHANT_ID" in error for error in errors))


class HealthEndpointTests(APITestCase):
    def test_liveness_and_readiness(self):
        live = self.client.get("/health/live/")
        ready = self.client.get("/health/ready/")
        self.assertEqual(live.status_code, 200)
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.data["components"], {"database": True, "cache": True})

    def test_production_check_rejects_development_settings(self):
        with self.assertRaisesRegex(CommandError, "Production readiness failed"):
            call_command("production_check")
