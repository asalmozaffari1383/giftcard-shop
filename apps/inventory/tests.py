from cryptography.fernet import Fernet
from django.test import SimpleTestCase, override_settings

from .models import DigitalItem


class EncryptedItemTests(SimpleTestCase):
    def test_round_trip_and_key_rotation(self):
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        item = DigitalItem()
        with override_settings(INVENTORY_FERNET_KEYS=[old_key]):
            item.set_secret("Gift-Card-123")
        self.assertNotIn(b"Gift-Card-123", bytes(item.encrypted_payload))
        with override_settings(INVENTORY_FERNET_KEYS=[new_key, old_key]):
            self.assertEqual(item.reveal_secret(), "Gift-Card-123")
