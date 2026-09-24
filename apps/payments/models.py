import uuid

from django.db import models
from django.db.models import Q

from apps.common.models import TimeStampedModel


class PaymentTransaction(TimeStampedModel):
    class Status(models.TextChoices):
        INITIATING = "INITIATING", "در حال درخواست"
        READY = "READY", "در انتظار پرداخت"
        VERIFIED = "VERIFIED", "تاییدشده"
        FAILED = "FAILED", "ناموفق"
        RECONCILIATION = "RECONCILIATION", "نیازمند بررسی/استرداد"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments")
    gateway = models.CharField(max_length=20, default="zarinpal")
    idempotency_key = models.CharField(max_length=80)
    authority = models.CharField(max_length=100, unique=True, null=True, blank=True)
    reference_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount_toman = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATING)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "idempotency_key"],
                                                name="payment_order_idempotency"),
                       models.CheckConstraint(condition=Q(amount_toman__gt=0),
                                              name="payment_amount_positive")]
        indexes = [models.Index(fields=["order", "status"])]


class PaymentEvent(models.Model):
    payment = models.ForeignKey(PaymentTransaction, on_delete=models.PROTECT, related_name="events")
    event = models.CharField(max_length=40)
    gateway_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["payment", "-created_at"])]


class PaymentRefund(models.Model):
    """Record an external full refund after an operator confirms settlement."""

    payment = models.OneToOneField(PaymentTransaction, on_delete=models.PROTECT, related_name="refund")
    external_reference = models.CharField(max_length=100, unique=True)
    recorded_by = models.ForeignKey("users.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
