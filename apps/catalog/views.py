from django.db.models import Avg, Count, Prefetch, Q
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.inventory.models import DigitalItem

from .models import Brand, Category, Product, ProductVariant
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    search_fields = ("title_fa", "sku", "brand__title_fa")
    ordering_fields = ("created_at", "title_fa")
    filterset_fields = ("category__slug", "brand__slug")

    def get_queryset(self):
        variants = ProductVariant.objects.filter(is_active=True).annotate(
            stock=Count("digital_items", filter=Q(digital_items__status=DigitalItem.Status.AVAILABLE)))
        return Product.objects.filter(is_active=True).select_related("brand", "category").annotate(
            rating_average=Avg("reviews__rating", filter=Q(reviews__status="APPROVED")),
            rating_count=Count("reviews", filter=Q(reviews__status="APPROVED"), distinct=True),
        ).prefetch_related(Prefetch("variants", queryset=variants)).order_by("-created_at", "-id")
