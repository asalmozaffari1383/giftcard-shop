from django.db import IntegrityError, transaction
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    filterset_fields = ("product",)

    def get_permissions(self):
        return [AllowAny()] if self.action == "list" else [IsAuthenticated()]

    def get_queryset(self):
        return Review.objects.filter(status=Review.Status.APPROVED).order_by("-created_at")

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError as exc:
            raise ValidationError("برای این محصول قبلاً نظر ثبت کرده‌اید.") from exc
