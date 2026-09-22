from rest_framework import serializers

from .models import Inquiry, Ticket, TicketMessage


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ("id", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class TicketSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "user", "subject", "status", "order", "messages", "created_at")
        read_only_fields = ("id", "status", "messages", "created_at")

    def validate_order(self, order):
        if order and order.user_id != self.context["request"].user.pk:
            raise serializers.ValidationError("سفارش متعلق به شما نیست.")
        return order


class InquirySerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        model = Inquiry
        fields = ("name", "phone_number", "body")

    def validate_phone_number(self, value):
        return self._normalize(value)

    @staticmethod
    def _normalize(value):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from apps.users.models import normalize_phone
        try:
            return normalize_phone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
