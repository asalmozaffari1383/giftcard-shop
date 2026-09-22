from rest_framework import serializers

from apps.catalog.models import Product
from apps.orders.models import Order

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ("id", "product", "rating", "body", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate_product(self, product):
        user = self.context["request"].user
        if not Order.objects.filter(user=user, status=Order.Status.COMPLETED,
                                    items__variant__product=product).exists():
            raise serializers.ValidationError("فقط خریداران این محصول می‌توانند نظر دهند.")
        return product
