import requests
from celery import shared_task
from django.conf import settings


def _send_template_sms(phone, template_id, token):
    if not settings.SMS_API_URL.startswith("https://") or not settings.SMS_API_KEY or not template_id:
        raise RuntimeError("SMS provider is not configured")
    local_phone = "0" + phone[3:]
    response = requests.post(
        settings.SMS_API_URL,
        headers={"Authorization": f"Bearer {settings.SMS_API_KEY}"},
        json={"receptor": local_phone, "template": template_id, "token": token},
        timeout=10,
    )
    response.raise_for_status()


@shared_task(autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_otp_sms(phone, code):
    """Send via a configured HTTPS template API; never log the OTP."""
    _send_template_sms(phone, settings.SMS_TEMPLATE_ID, code)


@shared_task(autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_order_completed_sms(phone, order_reference):
    """Notify the buyer after atomic digital fulfillment without exposing delivered codes."""
    _send_template_sms(phone, settings.SMS_ORDER_TEMPLATE_ID, order_reference)
