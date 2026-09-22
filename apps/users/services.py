import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError

from .models import OTPChallenge, User, normalize_phone
from .tasks import send_otp_sms


def _lock_phone(phone):
    """Serialize OTP actions even when no challenge row exists (PostgreSQL only)."""
    lock_id = int.from_bytes(hashlib.sha256(phone.encode()).digest()[:8], "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])


def _hash_code(phone, code):
    return hmac.new(settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


@transaction.atomic
def request_otp(phone):
    """Issue a five-minute OTP with a rolling three-request window."""
    phone = normalize_phone(phone)
    _lock_phone(phone)
    now = timezone.now()
    recent = OTPChallenge.objects.filter(phone_number=phone, created_at__gte=now - timedelta(minutes=5))
    if recent.count() >= 3:
        raise Throttled(wait=300, detail="تعداد درخواست بیش از حد مجاز است.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    OTPChallenge.objects.filter(phone_number=phone, consumed_at__isnull=True).update(consumed_at=now)
    OTPChallenge.objects.create(phone_number=phone, code_hash=_hash_code(phone, code),
                                expires_at=now + timedelta(minutes=5))
    transaction.on_commit(lambda: send_otp_sms.delay(phone, code))


def verify_otp(phone, code):
    """Consume once; failed attempts invalidate a challenge after five tries."""
    phone = normalize_phone(phone)
    with transaction.atomic():
        _lock_phone(phone)
        now = timezone.now()
        challenge = (OTPChallenge.objects.select_for_update().filter(
            phone_number=phone, consumed_at__isnull=True, expires_at__gt=now).order_by("-created_at").first())
        if not challenge or challenge.attempts >= 5:
            valid = False
            user = None
        else:
            challenge.attempts += 1
            valid = hmac.compare_digest(challenge.code_hash, _hash_code(phone, code))
            if valid or challenge.attempts >= 5:
                challenge.consumed_at = now
            challenge.save(update_fields=["attempts", "consumed_at"])
            user = None
            if valid:
                user, _ = User.objects.get_or_create(phone_number=phone, defaults={"is_verified": True})
                if not user.is_active:
                    valid = False
                elif not user.is_verified:
                    user.is_verified = True
                    user.save(update_fields=["is_verified"])
    if not valid:
        raise ValidationError("کد نامعتبر یا منقضی شده است.")
    return user
