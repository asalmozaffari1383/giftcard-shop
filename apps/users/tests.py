from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .models import normalize_phone


class IranianPhoneTests(SimpleTestCase):
    def test_normalizes_international_and_persian_digits(self):
        self.assertEqual(normalize_phone("۰۹۱۲ ۳۴۵-۶۷۸۹"), "+989123456789")
        self.assertEqual(normalize_phone("0098(912)3456789"), "+989123456789")

    def test_rejects_landline_or_wrong_length(self):
        for phone in ("02112345678", "0912345", "+9891234567890"):
            with self.subTest(phone=phone), self.assertRaises(ValidationError):
                normalize_phone(phone)
