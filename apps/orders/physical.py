from collections import Counter

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from apps.catalog.models import BundleComponent, Product
from apps.users.models import Address, LoyaltyEntry

from .models import Order, ShippingMethod, StockReservation


def prepare_physical_cart(lines, user, address_id, shipping_method_id):
    physical = [line for line in lines if line.variant.product.kind == "PHYSICAL"]
    if not physical:
        return {}, {}, 0, ""
    if len(physical) != len(lines):
        raise ValidationError("کالای آرشیو و کالای فیزیکی را در سفارش جداگانه بخرید.")
    address = Address.objects.filter(pk=address_id, user=user).first()
    method = ShippingMethod.objects.filter(pk=shipping_method_id, is_active=True).first()
    if not address or not method:
        raise ValidationError("آدرس و روش ارسال معتبر را انتخاب کنید.")
    product_ids = {line.variant.product_id for line in lines}
    components = list(BundleComponent.objects.filter(bundle_id__in=product_ids).select_related("product"))
    products = {product.pk: product for product in Product.objects.select_for_update().filter(
        pk__in=product_ids | {item.product_id for item in components}).order_by("pk")}
    demand = Counter()
    subtotal = 0
    for line in lines:
        product = products[line.variant.product_id]
        line.variant.product = product
        if not product.is_active or not line.variant.is_active:
            raise ValidationError("محصول غیرفعال است.")
        demand[product.pk] += line.quantity
        if product.is_bundle:
            pack = [item for item in components if item.bundle_id == product.pk]
            if not pack:
                raise ValidationError("اقلام این پک هنوز ثبت نشده‌اند.")
            for item in pack:
                component = products[item.product_id]
                if component.is_bundle or component.kind != "PHYSICAL" or not component.is_active:
                    raise ValidationError("اقلام پک قابل خرید نیستند.")
                demand[component.pk] += line.quantity * item.quantity
        subtotal += product.final_price * line.quantity
    if any(products[product_id].stock < amount for product_id, amount in demand.items()):
        raise ValidationError("موجودی یک یا چند کالا کافی نیست؛ تعداد را کاهش دهید.")
    snapshot = {field: getattr(address, field) for field in (
        "recipient_name", "phone_number", "province", "city", "address", "postal_code")}
    shipping = 0 if method.free_above_toman and subtotal >= method.free_above_toman else method.price_toman
    return demand, snapshot, shipping, method.title


def reserve_stock(order, demand):
    for product_id, amount in sorted(demand.items()):
        Product.objects.filter(pk=product_id).update(stock=F("stock") - amount)
        StockReservation.objects.create(order=order, product_id=product_id, quantity=amount)


def release_stock(order):
    reservations = list(order.stock_reservations.filter(state="RESERVED").order_by("product_id"))
    list(Product.objects.select_for_update().filter(pk__in=[item.product_id for item in reservations]).order_by("pk"))
    for item in reservations:
        Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
        item.state = "RELEASED"
        item.save(update_fields=["state"])


def reservation_complete(order):
    if not order.is_physical:
        return True
    return order.stock_reservations.filter(state="RESERVED").exists() and not order.stock_reservations.exclude(state="RESERVED").exists()


@transaction.atomic
def advance_order(order_id, target, tracking_code=""):
    order = Order.objects.select_for_update().get(pk=order_id)
    allowed = {Order.Status.PROCESSING: Order.Status.SHIPPED, Order.Status.SHIPPED: Order.Status.COMPLETED}
    if not order.is_physical or not order.paid_at or allowed.get(order.status) != target:
        raise ValidationError("تغییر وضعیت سفارش مجاز نیست.")
    if target == Order.Status.SHIPPED and not (tracking_code or order.tracking_code):
        raise ValidationError("کد رهگیری را پیش از ارسال ثبت کنید.")
    order.status = target
    if tracking_code:
        order.tracking_code = tracking_code
    order.save(update_fields=["status", "tracking_code", "updated_at"])
    if target == Order.Status.COMPLETED:
        LoyaltyEntry.objects.get_or_create(user=order.user, order=order, defaults={"points": order.total_toman // 10000})
    return order
