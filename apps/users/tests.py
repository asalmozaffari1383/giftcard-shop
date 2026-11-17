from unittest.mock import patch

import requests
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from .models import normalize_phone
from .tasks import _send_template_sms, send_order_completed_sms, send_otp_sms


class IranianPhoneTests(SimpleTestCase):
    def test_normalizes_international_and_persian_digits(self):
        self.assertEqual(normalize_phone("۰۹۱۲ ۳۴۵-۶۷۸۹"), "+989123456789")
        self.assertEqual(normalize_phone("0098(912)3456789"), "+989123456789")

    def test_rejects_landline_or_wrong_length(self):
        for phone in ("02112345678", "0912345", "+9891234567890"):
            with self.subTest(phone=phone), self.assertRaises(ValidationError):
                normalize_phone(phone)


@override_settings(SMS_PROVIDER="smsir", SMS_API_URL="https://api.sms.ir/v1/send/verify",
                   SMS_API_KEY="test-key", SMS_TEMPLATE_ID="123", SMS_ORDER_TEMPLATE_ID="456",
                   SMS_OTP_PARAMETER="CODE", SMS_ORDER_PARAMETER="ORDER_REFERENCE")
class SmsIrTests(SimpleTestCase):
    @patch("apps.users.tasks.requests.post")
    def test_otp_uses_smsir_template_contract(self, post):
        post.return_value.json.return_value = {"status": 1}
        send_otp_sms.run("+989123456789", "123456")
        post.assert_called_once_with(
            "https://api.sms.ir/v1/send/verify", headers={"x-api-key": "test-key"},
            json={"mobile": "09123456789", "templateId": 123,
                  "parameters": [{"name": "CODE", "value": "123456"}]}, timeout=10,
        )

    @patch("apps.users.tasks.requests.post")
    def test_order_notification_uses_its_own_template(self, post):
        post.return_value.json.return_value = {"status": 1}
        send_order_completed_sms.run("+989123456789", "ORDER-123")
        self.assertEqual(post.call_args.kwargs["json"], {
            "mobile": "09123456789", "templateId": 456,
            "parameters": [{"name": "ORDER_REFERENCE", "value": "ORDER-123"}],
        })

    @patch("apps.users.tasks.requests.post")
    def test_provider_rejection_is_not_treated_as_delivery(self, post):
        for result in ({"status": 0}, {}, []):
            with self.subTest(result=result), self.assertRaises(requests.RequestException):
                post.return_value.json.return_value = result
                _send_template_sms("+989123456789", "123", "123456", "CODE")

    @patch("apps.users.tasks.requests.post")
    def test_invalid_json_is_not_treated_as_delivery(self, post):
        post.return_value.json.side_effect = ValueError("Invalid JSON")
        with self.assertRaises(requests.RequestException):
            _send_template_sms("+989123456789", "123", "123456", "CODE")

    @patch("apps.users.tasks.requests.post")
    def test_invalid_template_is_rejected_before_request(self, post):
        for template_id in ("replace-me", "0", "-1"):
            with self.subTest(template_id=template_id), self.assertRaises(RuntimeError):
                _send_template_sms("+989123456789", template_id, "123456", "CODE")
        post.assert_not_called()

    @override_settings(SMS_PROVIDER="generic")
    @patch("apps.users.tasks.requests.post")
    def test_generic_provider_preserves_existing_contract(self, post):
        _send_template_sms("+989123456789", "login", "123456", "CODE")
        self.assertEqual(post.call_args.kwargs["headers"], {"Authorization": "Bearer test-key"})
        self.assertEqual(post.call_args.kwargs["json"], {
            "receptor": "09123456789", "template": "login", "token": "123456",
        })
