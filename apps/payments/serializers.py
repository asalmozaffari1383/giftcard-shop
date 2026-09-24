from rest_framework import serializers

from .models import PaymentRefund, PaymentTransaction


class PaymentRequestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    idempotency_key = serializers.RegexField(r"^[A-Za-z0-9._:-]{8,80}$")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ("id", "order", "gateway", "amount_toman", "status", "reference_id", "verified_at")


class RefundRecordSerializer(serializers.Serializer):
    external_reference = serializers.CharField(min_length=4, max_length=100, trim_whitespace=True)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ("id", "payment", "external_reference", "recorded_by", "created_at")
