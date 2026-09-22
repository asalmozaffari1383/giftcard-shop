import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Cart(TimeStampedModel):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="cart")


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_cart_variant"),
                       models.CheckConstraint(condition=Q(quantity__gt=0), name="cart_quantity_positive")]


class Coupon(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    percent_off = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    max_discount_toman = models.PositiveBigIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.percent_off > 100 or self.starts_at >= self.ends_at:
            raise ValidationError("تنظیمات تخفیف نامعتبر است.")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(percent_off__gte=1, percent_off__lte=100),
                                               name="coupon_percent_range")]


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار پرداخت"
        PROCESSING = "PROCESSING", "در حال پردازش"
        COMPLETED = "COMPLETED", "تکمیل‌شده"
        FAILED = "FAILED", "ناموفق"
        REFUNDED = "REFUNDED", "بازپرداخت‌شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="orders")
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


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price_toman = models.PositiveBigIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "variant"], name="unique_order_variant")]
