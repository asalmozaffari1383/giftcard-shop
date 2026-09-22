"""Zarinpal v4 adapter: only server-to-server verification authorizes delivery."""

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
        self.start_url = ("https://sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX
                          else "https://www.zarinpal.com") + "/pg/StartPay/"

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
        return authority, self.start_url + authority

    def verify(self, authority, amount_toman):
        data = self._post("verify", {"amount": amount_toman * 10, "authority": authority})
        try:
            code = int(data.get("code", -1))
        except (TypeError, ValueError) as exc:
            raise GatewayError("Malformed verification response") from exc
        return Verification(code in (100, 101), code, str(data.get("ref_id", "")))
