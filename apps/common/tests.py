from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APITestCase


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
