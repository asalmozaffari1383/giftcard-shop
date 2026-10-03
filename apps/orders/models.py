import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.common.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="cart")


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cart", "variant"], name="unique_cart_variant"),
            models.CheckConstraint(condition=Q(quantity__gte=1, quantity__lte=20),
                                   name="cart_quantity_range"),
        ]


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=40)
    percent_off = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    max_discount_toman = models.PositiveBigIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        invalid_percent = self.percent_off is not None and self.percent_off > 100
        invalid_dates = self.starts_at and self.ends_at and self.starts_at >= self.ends_at
        if invalid_percent or invalid_dates:
            raise ValidationError("تنظیمات تخفیف نامعتبر است.")

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("code"), name="coupon_code_ci_unique"),
            models.CheckConstraint(condition=Q(percent_off__gte=1, percent_off__lte=100),
                                   name="coupon_percent_range"),
            models.CheckConstraint(condition=Q(starts_at__lt=F("ends_at")), name="coupon_date_range"),
            models.CheckConstraint(condition=Q(usage_limit__gte=1), name="coupon_usage_limit_positive"),
            models.CheckConstraint(condition=Q(used_count__lte=F("usage_limit")),
                                   name="coupon_usage_within_limit"),
        ]


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار پرداخت"
        PROCESSING = "PROCESSING", "در حال پردازش"
        COMPLETED = "COMPLETED", "تکمیل‌شده"
        CANCELED = "CANCELED", "لغوشده"
        FAILED = "FAILED", "ناموفق"
        REFUNDED = "REFUNDED", "بازپرداخت‌شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="orders")
    idempotency_key = models.CharField(max_length=80, blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    subtotal_toman = models.PositiveBigIntegerField()
    discount_toman = models.PositiveBigIntegerField(default=0)
    total_toman = models.PositiveBigIntegerField()
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.PROTECT)
    expires_at = models.DateTimeField(db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"]),
                   models.Index(fields=["status", "expires_at"])]
        constraints = [
            models.UniqueConstraint(fields=["user", "idempotency_key"],
                                    condition=~Q(idempotency_key=""),
                                    name="order_user_idempotency"),
            models.CheckConstraint(condition=Q(discount_toman__lte=F("subtotal_toman")),
                                   name="order_discount_lte_subtotal"),
            models.CheckConstraint(condition=Q(subtotal_toman__gt=0, total_toman__gt=0),
                                   name="order_amounts_positive"),
            models.CheckConstraint(condition=Q(total_toman=F("subtotal_toman") - F("discount_toman")),
                                   name="order_total_consistency"),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)])
    unit_price_toman = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "variant"], name="unique_order_variant"),
            models.CheckConstraint(condition=Q(quantity__gte=1, quantity__lte=20),
                                   name="order_item_quantity_range"),
            models.CheckConstraint(condition=Q(unit_price_toman__gt=0),
                                   name="order_item_price_positive"),
        ]


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=12, blank=True)
    status = models.CharField(max_length=12, choices=Order.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [models.Index(fields=["order", "created_at"])]
