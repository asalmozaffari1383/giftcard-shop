from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from django.db.models import Sum
from apps.catalog.models import Product

from .models import Address, Profile, User, WishlistItem, normalize_phone


class PhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class VerifyOTPSerializer(PhoneSerializer):
    code = serializers.RegexField(r"^[0-9۰-۹٠-٩]{6}$")

    def validate_code(self, value):
        return value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("first_name", "last_name", "email", "birth_date")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    is_customer = serializers.BooleanField(read_only=True)
    loyalty_points = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "phone_number", "is_verified", "is_customer", "profile", "loyalty_points")

    def get_loyalty_points(self, obj) -> int:
        return obj.loyalty_entries.filter(order__status="COMPLETED").aggregate(total=Sum("points"))["total"] or 0


class AddressSerializer(serializers.ModelSerializer):
    phone_number = PhoneSerializer().fields["phone_number"]

    def validate_phone_number(self, value):
        return PhoneSerializer().validate_phone_number(value)

    def validate_postal_code(self, value):
        value = value.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
        if len(value) != 10 or not value.isascii() or not value.isdigit():
            raise serializers.ValidationError("کدپستی باید ۱۰ رقم باشد.")
        return value
    class Meta:
        model = Address
        fields = ("id", "title", "recipient_name", "phone_number", "province", "city", "address",
                  "postal_code", "is_default", "created_at")
        read_only_fields = ("id", "created_at")


class WishlistItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    product_title = serializers.CharField(source="product.title_fa", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = WishlistItem
        fields = ("id", "product", "product_title", "product_slug", "product_image", "created_at")
        read_only_fields = ("id", "created_at")

    def get_product_image(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.product.image:
            return request.build_absolute_uri(obj.product.image.url) if request else obj.product.image.url
        return None
