from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.inventory.models import DigitalItem
from apps.orders.models import Order
from apps.orders.services import _release_locked, dispatch_locked

from .gateways import GatewayError, ZarinpalGateway
from .models import PaymentEvent, PaymentRefund, PaymentTransaction


def initiate_payment(user, order_id, idempotency_key):
    """Reserve one gateway request per key without holding DB locks over HTTP."""
    gateway = ZarinpalGateway()
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(pk=order_id, user=user).first()
        if not order or order.status != Order.Status.PENDING or order.expires_at <= timezone.now():
            raise ValidationError("سفارش قابل پرداخت نیست.")
        existing = PaymentTransaction.objects.filter(order=order, idempotency_key=idempotency_key).first()
        if existing:
            if existing.status == PaymentTransaction.Status.READY:
                return existing, ZarinpalGateway().start_url + existing.authority
            raise ValidationError("درخواست پرداخت قبلاً ثبت شده است.")
        if order.payments.filter(status__in=(PaymentTransaction.Status.INITIATING,
                                             PaymentTransaction.Status.READY)).exists():
            raise ValidationError("یک درخواست پرداخت فعال برای این سفارش وجود دارد.")
        payment = PaymentTransaction.objects.create(order=order, idempotency_key=idempotency_key,
                                                     amount_toman=order.total_toman)
        PaymentEvent.objects.create(payment=payment, event="INITIATED")
    try:
        authority, url = gateway.request_payment(payment.amount_toman, _callback_url(payment), f"سفارش {order_id}")
    except GatewayError as exc:
        PaymentTransaction.objects.filter(pk=payment.pk, status=PaymentTransaction.Status.INITIATING).update(
            status=PaymentTransaction.Status.FAILED)
        PaymentEvent.objects.create(payment=payment, event="REQUEST_FAILED")
        raise APIException("درگاه پرداخت در دسترس نیست.") from exc
    with transaction.atomic():
        payment = PaymentTransaction.objects.select_for_update().get(pk=payment.pk)
        payment.authority = authority
        payment.status = PaymentTransaction.Status.READY
        payment.save(update_fields=["authority", "status", "updated_at"])
        PaymentEvent.objects.create(payment=payment, event="READY")
    return payment, url


def _callback_url(payment):
    from django.conf import settings
    return f"{settings.PUBLIC_BASE_URL}/api/v1/payments/callback/{payment.id}/"


def verify_callback(payment_id, authority, gateway_status):
    """Untrusted callback only triggers remote verification; fulfillment is idempotent."""
    payment = PaymentTransaction.objects.select_related("order").filter(pk=payment_id).first()
    if not payment or payment.authority != authority or payment.status not in (
            PaymentTransaction.Status.READY, PaymentTransaction.Status.VERIFIED):
        raise ValidationError("تراکنش نامعتبر است.")
    if payment.status == PaymentTransaction.Status.VERIFIED:
        return payment
    PaymentEvent.objects.create(payment=payment, event="CALLBACK_RECEIVED")
    if gateway_status != "OK":
        raise ValidationError("پرداخت توسط درگاه تایید نشد.")
    try:
        result = ZarinpalGateway().verify(authority, payment.amount_toman)
    except GatewayError as exc:
        raise APIException("استعلام درگاه ناموفق بود؛ دوباره تلاش کنید.") from exc
    PaymentEvent.objects.create(payment=payment, event="VERIFY_RESPONSE", gateway_code=result.code)
    if not result.successful or not result.reference_id:
        raise ValidationError("پرداخت تایید نشد.")
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=payment.order_id)
        payment = PaymentTransaction.objects.select_for_update().get(pk=payment_id)
        if payment.status == PaymentTransaction.Status.VERIFIED:
            return payment
        if payment.authority != authority or payment.amount_toman != order.total_toman:
            raise ValidationError("مبلغ یا شناسه پرداخت مغایرت دارد.")
        if order.status != Order.Status.PENDING or order.expires_at <= timezone.now():
            payment.status = PaymentTransaction.Status.RECONCILIATION
            payment.reference_id = result.reference_id
            payment.verified_at = timezone.now()
            payment.save(update_fields=["status", "reference_id", "verified_at", "updated_at"])
            PaymentEvent.objects.create(payment=payment, event="REFUND_REQUIRED")
            return payment
        if order.payments.filter(status=PaymentTransaction.Status.VERIFIED).exists():
            raise ValidationError("سفارش قبلاً پرداخت شده است.")
        if any(DigitalItem.objects.filter(reserved_order=order, variant=item.variant,
                                          status=DigitalItem.Status.RESERVED).count() != item.quantity
               for item in order.items.select_related("variant")):
            payment.status = PaymentTransaction.Status.RECONCILIATION
            payment.reference_id = result.reference_id
            payment.verified_at = timezone.now()
            payment.save(update_fields=["status", "reference_id", "verified_at", "updated_at"])
            PaymentEvent.objects.create(payment=payment, event="FULFILLMENT_REVIEW_REQUIRED")
            return payment
        order.status = Order.Status.PROCESSING
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at", "updated_at"])
        dispatch_locked(order)
        payment.status = PaymentTransaction.Status.VERIFIED
        payment.reference_id = result.reference_id
        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "reference_id", "verified_at", "updated_at"])
        PaymentEvent.objects.create(payment=payment, event="FULFILLED", gateway_code=result.code)
    return payment


@transaction.atomic
def record_external_refund(payment_id, external_reference, admin):
    """Audit an already completed external refund; does not call the gateway."""
    payment_info = PaymentTransaction.objects.filter(pk=payment_id).values("order_id").first()
    if not payment_info:
        raise ValidationError("تراکنش یافت نشد.")
    order = Order.objects.select_for_update().get(pk=payment_info["order_id"])
    payment = PaymentTransaction.objects.select_for_update().get(pk=payment_id)
    if payment.status not in (PaymentTransaction.Status.VERIFIED, PaymentTransaction.Status.RECONCILIATION):
        raise ValidationError("این پرداخت قابل ثبت استرداد نیست.")
    if PaymentRefund.objects.filter(payment=payment).exists():
        raise ValidationError("استرداد قبلاً ثبت شده است.")
    if PaymentRefund.objects.filter(external_reference=external_reference).exists():
        raise ValidationError("شناسه استرداد قبلاً ثبت شده است.")
    if order.status == Order.Status.PENDING:
        _release_locked(order)
    if order.status not in (Order.Status.COMPLETED, Order.Status.FAILED):
        raise ValidationError("وضعیت سفارش برای استرداد نامعتبر است.")
    refund = PaymentRefund.objects.create(payment=payment, external_reference=external_reference,
                                          recorded_by=admin)
    if payment.status == PaymentTransaction.Status.VERIFIED or order.status == Order.Status.FAILED:
        order.status = Order.Status.REFUNDED
        order.save(update_fields=["status", "updated_at"])
    PaymentEvent.objects.create(payment=payment, event="REFUND_RECORDED")
    return refund
