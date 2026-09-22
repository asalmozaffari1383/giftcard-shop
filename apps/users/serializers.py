from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Profile, User, normalize_phone


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
        fields = ("first_name", "last_name", "email")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    is_customer = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "phone_number", "is_verified", "is_customer", "profile")
