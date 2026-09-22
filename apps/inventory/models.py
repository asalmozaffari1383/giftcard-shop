from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.common.models import TimeStampedModel
from .crypto import cipher


class DigitalItem(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "موجود"
        RESERVED = "RESERVED", "رزرو"
        SOLD = "SOLD", "فروخته‌شده"

    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="digital_items")
    encrypted_payload = models.BinaryField(editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.AVAILABLE)
    reserved_order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.PROTECT,
                                       related_name="reserved_codes")
    sold_order_item = models.ForeignKey("orders.OrderItem", null=True, blank=True,
                                        on_delete=models.PROTECT, related_name="digital_items")

    def set_secret(self, plaintext):
        if not plaintext or not plaintext.strip():
            raise ValidationError("کد نمی‌تواند خالی باشد.")
        self.encrypted_payload = cipher().encrypt(plaintext.encode("utf-8"))

    def reveal_secret(self):
        return cipher().decrypt(bytes(self.encrypted_payload)).decode("utf-8")

    def clean(self):
        if not self.encrypted_payload:
            raise ValidationError("کد الزامی است.")

    class Meta:
        constraints = [models.CheckConstraint(
            condition=(Q(status="AVAILABLE", reserved_order__isnull=True, sold_order_item__isnull=True) |
                       Q(status="RESERVED", reserved_order__isnull=False, sold_order_item__isnull=True) |
                       Q(status="SOLD", reserved_order__isnull=True, sold_order_item__isnull=False)),
            name="digital_item_state_consistency")]
        indexes = [models.Index(fields=["variant", "status", "id"]),
                   models.Index(fields=["reserved_order", "status"])]
