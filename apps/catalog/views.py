import hashlib
from html import escape

from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
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

    @action(detail=True, methods=("get",), permission_classes=(AllowAny,), url_path="artwork")
    def artwork(self, request, slug=None):
        """Return a deterministic, copyright-safe SVG cover for a product."""
        product = self.get_object()
        digest = hashlib.sha256(product.slug.encode()).hexdigest()
        palettes = (
            ("#5B35D5", "#9878FF", "#EEE9FF"), ("#0B766E", "#33B6A5", "#E1FAF5"),
            ("#B64166", "#F27A9B", "#FFE8EF"), ("#175CA8", "#4D9BE8", "#E5F2FF"),
            ("#A45814", "#F0A648", "#FFF1DC"), ("#343A52", "#717A9D", "#EEF0F7"),
        )
        primary, secondary, pale = palettes[int(digest[:2], 16) % len(palettes)]
        words = product.title_fa.split()
        lines = []
        current = []
        for word in words:
            if len(" ".join((*current, word))) > 27 and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        lines = lines[:3]
        text_nodes = "".join(
            f'<text x="560" y="{300 + index * 62}" text-anchor="middle" '
            f'font-family="Tahoma, Arial, sans-serif" font-size="42" font-weight="800" '
            f'fill="#FFFFFF" direction="rtl">{escape(line)}</text>'
            for index, line in enumerate(lines)
        )
        brand = escape(product.brand.title_fa if product.brand else "محصول دیجیتال")
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="760" viewBox="0 0 1120 760">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{primary}"/><stop offset="1" stop-color="{secondary}"/></linearGradient><filter id="shadow"><feDropShadow dx="0" dy="24" stdDeviation="24" flood-opacity=".25"/></filter></defs>
<rect width="1120" height="760" rx="50" fill="{pale}"/><circle cx="90" cy="95" r="210" fill="{secondary}" opacity=".16"/><circle cx="1030" cy="690" r="270" fill="{primary}" opacity=".13"/>
<g filter="url(#shadow)"><rect x="120" y="105" width="880" height="550" rx="48" fill="url(#bg)"/><circle cx="850" cy="205" r="100" fill="#fff" opacity=".09"/><path d="M120 520C330 420 460 690 1000 430V655H120Z" fill="#fff" opacity=".08"/></g>
<rect x="430" y="180" width="260" height="54" rx="27" fill="#fff" opacity=".16"/><text x="560" y="216" text-anchor="middle" font-family="Tahoma, Arial, sans-serif" font-size="24" font-weight="700" fill="#fff">{brand}</text>
{text_nodes}<text x="560" y="570" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" letter-spacing="5" fill="#fff" opacity=".72">DIGITAL PRODUCT</text>
</svg>'''
        response = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
        response["Cache-Control"] = "public, max-age=604800, immutable"
        return response

    def get_queryset(self):
        variants = ProductVariant.objects.filter(is_active=True).annotate(
            stock=Count("digital_items", filter=Q(digital_items__status=DigitalItem.Status.AVAILABLE)))
        return Product.objects.filter(is_active=True).select_related("brand", "category").annotate(
            rating_average=Avg("reviews__rating", filter=Q(reviews__status="APPROVED")),
            rating_count=Count("reviews", filter=Q(reviews__status="APPROVED"), distinct=True),
        ).prefetch_related(Prefetch("variants", queryset=variants)).order_by("-created_at", "-id")
