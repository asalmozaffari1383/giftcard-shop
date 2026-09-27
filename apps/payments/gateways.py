"""Zarinpal v4 adapter: only server-to-server verification authorizes delivery."""

import secrets
from dataclasses import dataclass

import requests
from django.conf import settings


class GatewayError(Exception):
    pass


@dataclass(frozen=True)
class Verification:
    successful: bool
    code: int
    reference_id: str = ""


class ZarinpalGateway:
    def __init__(self):
        if not settings.ZARINPAL_MERCHANT_ID:
            raise GatewayError("Zarinpal merchant ID is not configured")
        host = "sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "api.zarinpal.com"
        self.api_base = f"https://{host}/pg/v4/payment"
        self.start_url = self.payment_url("")

    @staticmethod
    def payment_url(authority, callback_url=None):
        base = "https://sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "https://www.zarinpal.com"
        return f"{base}/pg/StartPay/{authority}"

    def _post(self, action, payload):
        try:
            response = requests.post(f"{self.api_base}/{action}.json",
                                     json={"merchant_id": settings.ZARINPAL_MERCHANT_ID, **payload}, timeout=10)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
                raise ValueError("Malformed gateway response")
            return payload["data"]
        except (requests.RequestException, ValueError) as exc:
            raise GatewayError("Gateway communication failed") from exc

    def request_payment(self, amount_toman, callback_url, description):
        data = self._post("request", {"amount": amount_toman * 10, "currency": "IRR",
                                      "callback_url": callback_url, "description": description})
        if data.get("code") != 100 or not data.get("authority"):
            raise GatewayError("Gateway rejected the payment request")
        authority = str(data["authority"])
        return authority, self.payment_url(authority)

    def verify(self, authority, amount_toman):
        data = self._post("verify", {"amount": amount_toman * 10, "authority": authority})
        try:
            code = int(data.get("code", -1))
        except (TypeError, ValueError) as exc:
            raise GatewayError("Malformed verification response") from exc
        return Verification(code in (100, 101), code, str(data.get("ref_id", "")))


class MockGateway:
    """Local-only gateway that exercises callback verification and fulfillment."""

    @staticmethod
    def payment_url(authority, callback_url=None):
        if not callback_url:
            raise GatewayError("Mock callback URL is required")
        separator = "&" if "?" in callback_url else "?"
        return f"{callback_url}{separator}Authority={authority}&Status=OK"

    def request_payment(self, amount_toman, callback_url, description):
        authority = f"mock-{secrets.token_urlsafe(24)}"
        return authority, self.payment_url(authority, callback_url)

    def verify(self, authority, amount_toman):
        reference = f"MOCK-{secrets.randbelow(10**10):010d}"
        return Verification(True, 100, reference)


def get_gateway():
    return MockGateway() if settings.PAYMENT_GATEWAY == "mock" else ZarinpalGateway()
