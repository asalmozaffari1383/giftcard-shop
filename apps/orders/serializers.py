import jdatetime
from django.utils import timezone
from rest_framework import serializers

from apps.catalog.models import ProductVariant

from .models import CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.filter(is_active=True, product__is_active=True))
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    price_toman = serializers.IntegerField(source="variant.price_toman", read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "variant", "quantity", "price_toman")


class CheckoutSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)


class OrderItemSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)
    codes = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "sku", "quantity", "unit_price_toman", "codes")

    def get_codes(self, obj) -> list[str]:
        if not self.context.get("include_codes") or obj.order.status != Order.Status.COMPLETED:
            return []
        request = self.context.get("request")
        if not request or request.user.pk != obj.order.user_id:
            return []
        return [code.reveal_secret() for code in obj.digital_codes_cache]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    created_at_jalali = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ("id", "status", "subtotal_toman", "discount_toman", "total_toman",
                  "created_at", "created_at_jalali", "expires_at", "paid_at", "items")

    def get_created_at_jalali(self, obj) -> str:
        return jdatetime.datetime.fromgregorian(datetime=timezone.localtime(obj.created_at)).strftime("%Y/%m/%d %H:%M")
