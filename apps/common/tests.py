from rest_framework.test import APITestCase


class HealthEndpointTests(APITestCase):
    def test_liveness_and_readiness(self):
        live = self.client.get("/health/live/")
        ready = self.client.get("/health/ready/")
        self.assertEqual(live.status_code, 200)
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.data["components"], {"database": True, "cache": True})
