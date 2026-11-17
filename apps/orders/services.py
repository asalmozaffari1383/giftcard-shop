import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.catalog.models import ProductVariant
from apps.inventory.models import DigitalItem

from .models import Cart, Coupon, Order, OrderItem
from .physical import prepare_physical_cart, release_stock, reserve_stock

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,80}$")


def get_or_create_cart(user, *, lock=False):
    """Create a user's single cart safely; optionally serialize mutations by user row."""
    if lock:
        get_user_model().objects.select_for_update().only("pk").get(pk=user.pk)
    try:
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=user)
    except IntegrityError:
        cart = Cart.objects.get(user=user)
    if lock:
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
    return cart


def _release_locked(order, *, target_status=Order.Status.FAILED):
    """Release only unpaid reservations while holding the order row lock."""
    if order.status != Order.Status.PENDING:
        return
    release_stock(order)
    DigitalItem.objects.filter(reserved_order=order, status=DigitalItem.Status.RESERVED).update(
        status=DigitalItem.Status.AVAILABLE, reserved_order=None)
    if order.coupon_id:
        Coupon.objects.filter(pk=order.coupon_id, used_count__gt=0).update(used_count=F("used_count") - 1)
    order.status = target_status
    order.save(update_fields=["status", "updated_at"])


@transaction.atomic
def cancel_order(user, order_id):
    """Cancel an unpaid order and release only its own reserved inventory."""
    order = Order.objects.select_for_update().filter(pk=order_id, user=user).first()
    if not order:
        raise ValidationError("سفارش یافت نشد.")
    if order.status != Order.Status.PENDING:
        raise ValidationError("فقط سفارش در انتظار پرداخت قابل لغو است.")
    if order.payments.filter(status="VERIFIED").exists():
        raise ValidationError("سفارش پرداخت‌شده قابل لغو نیست.")
    _release_locked(order, target_status=Order.Status.CANCELED)
    return order


@transaction.atomic
def checkout(user, coupon_code="", idempotency_key="", address_id=None, shipping_method_id=None):
    """Snapshot prices, reserve exact codes and coupon atomically for 15 minutes."""
    idempotency_key = idempotency_key.strip()
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key):
        raise ValidationError("هدر Idempotency-Key معتبر نیست.")
    cart = get_or_create_cart(user, lock=True)
    existing = Order.objects.filter(user=user, idempotency_key=idempotency_key).first()
    if existing:
        return existing, False
    lines = list(cart.items.select_related("variant", "variant__product").order_by("variant_id"))
    if not lines:
        raise ValidationError("سبد خرید خالی است.")
    coupon = None
    if coupon_code:
        coupon = Coupon.objects.select_for_update().filter(code__iexact=coupon_code.strip()).first()
        now = timezone.now()
        if not coupon or not coupon.is_active or not coupon.starts_at <= now < coupon.ends_at or coupon.used_count >= coupon.usage_limit:
            raise ValidationError("کد تخفیف نامعتبر است.")
        if coupon.assigned_user_id and coupon.assigned_user_id != user.pk:
            raise ValidationError("کد تخفیف متعلق به این حساب نیست.")
        birthday = getattr(getattr(user, "profile", None), "birth_date", None)
        today = timezone.localdate()
        if coupon.birthday_only and (not birthday or (birthday.month, birthday.day) != (today.month, today.day)):
            raise ValidationError("کد تولد فقط در روز تولد قابل استفاده است.")
    variants = {variant.pk: variant for variant in ProductVariant.objects.select_for_update(of=("self",)).select_related(
        "product").filter(pk__in=[line.variant_id for line in lines]).order_by("pk")}
    subtotal = 0
    selected = []
    demand, shipping_address, shipping_toman, shipping_method = prepare_physical_cart(
        lines, user, address_id, shipping_method_id)
    for line in lines:
        variant = variants[line.variant_id]
        if not variant.is_active or not variant.product.is_active or line.quantity > 20:
            raise ValidationError("کالا غیرفعال است یا تعداد آن مجاز نیست.")
        if demand:
            variant.product = line.variant.product
            variant.price_toman = variant.product.final_price
        codes = [] if demand else list(DigitalItem.objects.select_for_update(skip_locked=True).filter(
            variant=variant, status=DigitalItem.Status.AVAILABLE).order_by("pk")[:line.quantity])
        if not demand and len(codes) != line.quantity:
            raise ValidationError(f"موجودی {variant.sku} کافی نیست.")
        selected.append((line, variant, codes))
        subtotal += variant.price_toman * line.quantity
    discount = min(coupon.amount_off or subtotal * coupon.percent_off // 100, subtotal,
                   coupon.max_discount_toman if coupon.max_discount_toman is not None else subtotal) if coupon else 0
    if subtotal - discount < 1:
        raise ValidationError("مبلغ نهایی باید مثبت باشد.")
    order = Order.objects.create(user=user, subtotal_toman=subtotal, discount_toman=discount,
                                 total_toman=subtotal - discount + shipping_toman, coupon=coupon,
                                 is_physical=bool(demand), shipping_toman=shipping_toman,
                                 shipping_address=shipping_address, shipping_method=shipping_method,
                                 idempotency_key=idempotency_key,
                                 expires_at=timezone.now() + timedelta(minutes=15))
    for line, variant, codes in selected:
        OrderItem.objects.create(order=order, variant=variant, quantity=line.quantity,
                                 unit_price_toman=variant.price_toman, product_title_snapshot=variant.product.title_fa,
                                 variant_label_snapshot=variant.label)
        DigitalItem.objects.filter(pk__in=[code.pk for code in codes]).update(
            status=DigitalItem.Status.RESERVED, reserved_order=order)
    reserve_stock(order, demand)
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
    cart.items.all().delete()
    return order, True


def dispatch_locked(order):
    """Assign exactly the reserved codes; caller must lock the order in an atomic block."""
    if order.status != Order.Status.PROCESSING:
        raise ValidationError("سفارش قابل تحویل نیست.")
    if order.is_physical:
        order.stock_reservations.filter(state="RESERVED").update(state="CONSUMED")
        return
    for line in order.items.order_by("pk"):
        codes = list(DigitalItem.objects.select_for_update().filter(
            reserved_order=order, variant=line.variant, status=DigitalItem.Status.RESERVED).order_by("pk"))
        if len(codes) != line.quantity:
            raise ValidationError("تعداد کدهای رزروشده مغایرت دارد؛ نیاز به بررسی دستی است.")
        for code in codes:
            code.status = DigitalItem.Status.SOLD
            code.reserved_order = None
            code.sold_order_item = line
            code.save(update_fields=["status", "reserved_order", "sold_order_item", "updated_at"])
    order.status = Order.Status.COMPLETED
    order.save(update_fields=["status", "updated_at"])


@transaction.atomic
def expire_order(order_id):
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.expires_at <= timezone.now():
        _release_locked(order)
