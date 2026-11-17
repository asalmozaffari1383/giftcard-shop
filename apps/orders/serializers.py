import jdatetime
from django.utils import timezone
from rest_framework import serializers

from apps.catalog.models import ProductVariant

from .models import CartItem, Order, OrderItem, OrderStatusHistory, ShippingMethod


class CartItemSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True, product__is_active=True))
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    price_toman = serializers.SerializerMethodField()
    product_kind = serializers.CharField(source="variant.product.kind", read_only=True)
    product_title = serializers.CharField(source="variant.product.title_fa", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    variant_label = serializers.CharField(source="variant.label", read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "variant", "quantity", "price_toman", "product_title", "product_slug", "variant_label", "product_kind")

    def get_price_toman(self, obj) -> int:
        return obj.variant.product.final_price if obj.variant.product.kind == "PHYSICAL" else obj.variant.price_toman


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class CheckoutSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    address_id = serializers.IntegerField(required=False, allow_null=True)
    shipping_method_id = serializers.IntegerField(required=False, allow_null=True)


class OrderItemSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)
    product_title = serializers.SerializerMethodField()
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    variant_label = serializers.SerializerMethodField()
    variant = serializers.IntegerField(source="variant_id", read_only=True)
    region = serializers.CharField(source="variant.region", read_only=True)
    codes = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "variant", "sku", "product_title", "product_slug", "variant_label", "region",
                  "quantity", "unit_price_toman", "codes")

    def get_product_title(self, obj) -> str:
        return obj.product_title_snapshot or obj.variant.product.title_fa

    def get_variant_label(self, obj) -> str:
        return obj.variant_label_snapshot or obj.variant.label

    def get_codes(self, obj) -> list[str]:
        if obj.order.is_physical or not self.context.get("include_codes") or obj.order.status != Order.Status.COMPLETED:
            return []
        request = self.context.get("request")
        if not request or request.user.pk != obj.order.user_id:
            return []
        return [code.reveal_secret() for code in obj.digital_codes_cache]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ("id", "previous_status", "status", "label", "created_at")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    created_at_jalali = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "status", "subtotal_toman", "discount_toman", "total_toman",
                  "shipping_toman", "shipping_address", "shipping_method", "tracking_code", "is_physical",
                  "created_at", "created_at_jalali", "expires_at", "paid_at", "items", "status_history")

    def get_created_at_jalali(self, obj) -> str:
        return jdatetime.datetime.fromgregorian(datetime=timezone.localtime(obj.created_at)).strftime("%Y/%m/%d %H:%M")


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = ("id", "title", "price_toman", "free_above_toman")
