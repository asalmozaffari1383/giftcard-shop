import requests
from celery import shared_task
from django.conf import settings


def _send_template_sms(phone, template_id, token, parameter_name):
    if not settings.SMS_API_URL.startswith("https://") or not settings.SMS_API_KEY or not template_id:
        raise RuntimeError("SMS provider is not configured")
    local_phone = "0" + phone[3:]
    if settings.SMS_PROVIDER == "smsir":
        try:
            numeric_template_id = int(template_id)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("SMS.ir template ID must be a positive integer") from exc
        if numeric_template_id < 1 or not parameter_name:
            raise RuntimeError("SMS.ir template ID and parameter name must be configured")
        response = requests.post(
            settings.SMS_API_URL,
            headers={"x-api-key": settings.SMS_API_KEY},
            json={"mobile": local_phone, "templateId": numeric_template_id,
                  "parameters": [{"name": parameter_name, "value": str(token)}]},
            timeout=10,
        )
        response.raise_for_status()
        try:
            result = response.json()
        except ValueError as exc:
            raise requests.RequestException("SMS.ir returned an invalid response") from exc
        if not isinstance(result, dict) or result.get("status") != 1:
            raise requests.RequestException("SMS.ir did not accept the template message")
        return
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
    _send_template_sms(phone, settings.SMS_TEMPLATE_ID, code, settings.SMS_OTP_PARAMETER)


@shared_task(autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def send_order_completed_sms(phone, order_reference):
    """Notify the buyer after atomic digital fulfillment without exposing delivered codes."""
    _send_template_sms(phone, settings.SMS_ORDER_TEMPLATE_ID, order_reference, settings.SMS_ORDER_PARAMETER)
