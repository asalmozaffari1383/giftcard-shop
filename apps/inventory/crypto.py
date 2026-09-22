from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


def cipher():
    """First key encrypts; older keys remain usable for rotation."""
    return MultiFernet([Fernet(key.encode()) for key in settings.INVENTORY_FERNET_KEYS])
