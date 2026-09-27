from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.catalog.models import Product

from .models import Review
from .serializers import ReviewProductOptionSerializer, ReviewSerializer


class ReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = ReviewSerializer
    filterset_fields = ("product",)

    def get_permissions(self):
        if self.action in ("list", "retrieve") and self.request.query_params.get("mine") != "1":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.select_related("product", "user").order_by("-created_at")
        if self.action == "list" and self.request.query_params.get("mine") == "1":
            return queryset.filter(user=self.request.user)
        if self.action == "list" or not self.request.user.is_authenticated:
            return queryset.filter(status=Review.Status.APPROVED)
        return queryset.filter(Q(status=Review.Status.APPROVED) | Q(user=self.request.user))

    @action(detail=False, methods=["get"], url_path="eligible-products")
    def eligible_products(self, request):
        products = Product.objects.filter(
            is_active=True,
            variants__orderitem__order__user=request.user,
            variants__orderitem__order__status="COMPLETED",
        ).exclude(reviews__user=request.user).distinct().order_by("title_fa")
        return Response(ReviewProductOptionSerializer(products, many=True).data)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError as exc:
            raise ValidationError("برای این محصول قبلاً نظر ثبت کرده‌اید.") from exc

    def perform_update(self, serializer):
        if serializer.instance.user_id != self.request.user.pk:
            raise ValidationError("فقط نویسندهٔ نظر می‌تواند آن را ویرایش کند.")
        serializer.save(status=Review.Status.PENDING)

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.pk:
            raise ValidationError("فقط نویسندهٔ نظر می‌تواند آن را حذف کند.")
        instance.delete()
