import hmac
from urllib.parse import quote, urlencode
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.inventory.models import DigitalItem


class FeedQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=500, default=100)
    key = serializers.CharField(required=False, write_only=True)


class FeedProductSerializer(serializers.Serializer):
    page_unique_id = serializers.CharField()
    product_id = serializers.CharField()
    title = serializers.CharField()
    price = serializers.IntegerField()
    availability = serializers.CharField()
    old_price = serializers.IntegerField(allow_null=True)
    page_url = serializers.URLField()


class TorobFeedView(generics.GenericAPIView):
    """Partner JSON v1-style variant feed; prices are whole Tomans."""

    permission_classes = [AllowAny]
    serializer_class = FeedProductSerializer
    queryset = ProductVariant.objects.none()
    pagination_size = 100

    @staticmethod
    def _is_authorized(request):
        supplied = request.headers.get("X-Feed-Key", "") or request.query_params.get("key", "")
        return bool(settings.TOROB_FEED_KEY and hmac.compare_digest(supplied, settings.TOROB_FEED_KEY))

    @extend_schema(parameters=[FeedQuerySerializer], responses=FeedProductSerializer(many=True))
    def get(self, request):
        if not self._is_authorized(request):
            raise PermissionDenied("کلید فید نامعتبر است.")
        query = FeedQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = query.validated_data["page"]
        page_size = query.validated_data["page_size"]
        variants = ProductVariant.objects.filter(
            is_active=True, product__is_active=True, price_toman__gt=0,
        ).select_related(
            "product").annotate(stock=Count("digital_items", filter=Q(
                digital_items__status=DigitalItem.Status.AVAILABLE))).order_by("-created_at", "-pk")
        total = variants.count()
        batch = list(variants[(page - 1) * page_size:page * page_size])
        campaign_query = urlencode({"utm_source": "torob", "utm_medium": "cpc", "utm_campaign": "products"})
        data = [{"page_unique_id": variant.sku, "product_id": variant.sku,
                 "title": f"{variant.product.title_fa} - {variant.label} ({variant.region})",
                 "price": variant.price_toman, "availability": "instock" if variant.stock else "outofstock",
                 "old_price": variant.old_price_toman,
                 "page_url": (f"{settings.FRONTEND_URL}/products/{quote(variant.product.slug)}/"
                              f"?variant={variant.pk}&{campaign_query}")} for variant in batch]
        if request.query_params.get("format") == "xml":
            root = Element("products")
            for product in data:
                element = SubElement(root, "product")
                for key, value in product.items():
                    SubElement(element, key).text = "" if value is None else str(value)
            response = HttpResponse(tostring(root, encoding="utf-8", xml_declaration=True),
                                    content_type="application/xml; charset=utf-8")
        else:
            response = Response(data)
        response["Cache-Control"] = "private, no-store"
        response["X-Total-Count"] = str(total)
        response["X-Page"] = str(page)
        response["X-Page-Size"] = str(page_size)
        return response
