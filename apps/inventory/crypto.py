import hashlib
import hmac

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def cipher():
    """First key encrypts; older keys remain usable for rotation."""
    return MultiFernet([Fernet(key.encode()) for key in settings.INVENTORY_FERNET_KEYS])


def secret_fingerprint(plaintext):
    """Create a non-reversible stable identifier used to reject duplicate secrets."""
    return hmac.new(settings.INVENTORY_FINGERPRINT_KEY.encode(), plaintext.encode("utf-8"),
                    hashlib.sha256).hexdigest()
