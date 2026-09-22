import requests
from celery import shared_task
from django.conf import settings


@shared_task(autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_otp_sms(phone, code):
    """Send via a configured HTTPS template API; never log the OTP."""
    if not settings.SMS_API_URL.startswith("https://") or not settings.SMS_API_KEY:
        raise RuntimeError("SMS provider is not configured")
    local_phone = "0" + phone[3:]
    response = requests.post(settings.SMS_API_URL,
                             headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"},
                             json={"receptor": local_phone, "template": settings.SMS_TEMPLATE_ID, "token": code},
                             timeout=10)
    response.raise_for_status()
