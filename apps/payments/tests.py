from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .gateways import GatewayError, ZarinpalGateway


@override_settings(ZARINPAL_MERCHANT_ID="merchant", ZARINPAL_SANDBOX=True)
class GatewayTests(SimpleTestCase):
    @patch("apps.payments.gateways.requests.post")
    def test_request_converts_toman_to_rial(self, post):
        post.return_value.json.return_value = {"data": {"code": 100, "authority": "ABC"}}
        authority, url = ZarinpalGateway().request_payment(25000, "https://shop.test/callback", "order")
        self.assertEqual(authority, "ABC")
        self.assertTrue(url.endswith("/ABC"))
        self.assertEqual(post.call_args.kwargs["json"]["amount"], 250000)
        self.assertEqual(post.call_args.kwargs["json"]["currency"], "IRR")

    @patch("apps.payments.gateways.requests.post")
    def test_verify_requires_successful_gateway_response(self, post):
        post.return_value.json.return_value = {"data": {"code": -22}}
        self.assertFalse(ZarinpalGateway().verify("ABC", 25000).successful)

    @patch("apps.payments.gateways.requests.post")
    def test_gateway_error_does_not_authorize_payment(self, post):
        import requests
        post.side_effect = requests.Timeout()
        with self.assertRaises(GatewayError):
            ZarinpalGateway().verify("ABC", 25000)
