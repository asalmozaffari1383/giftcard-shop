from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from .models import Brand, Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "parent", "title_fa", "slug")


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "title_fa", "slug")


class VariantSerializer(serializers.ModelSerializer):
    stock = serializers.SerializerMethodField()
    price_toman = serializers.SerializerMethodField()
    old_price_toman = serializers.SerializerMethodField()
    price_rial = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "label", "face_value", "currency", "region",
                  "price_toman", "price_rial", "old_price_toman", "stock")

    def get_price_rial(self, obj) -> int:
        return self.get_price_toman(obj) * 10

    def get_stock(self, obj) -> int:
        return obj.product.available_quantity if obj.product.kind == "PHYSICAL" else getattr(obj, "stock", 0)

    def get_price_toman(self, obj) -> int:
        return obj.product.final_price if obj.product.kind == "PHYSICAL" else obj.price_toman

    def get_old_price_toman(self, obj) -> int | None:
        if obj.product.kind == "PHYSICAL":
            return obj.product.price if obj.product.final_price < obj.product.price else None
        return obj.old_price_toman


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    variants = VariantSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    rating_average = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True, allow_null=True)
    rating_count = serializers.IntegerField(read_only=True)
    final_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "sku", "title_fa", "slug", "description", "image", "images", "price",
                  "discount", "final_price", "stock", "attributes", "tags", "is_bundle", "bundle_items",
                  "kind", "age_group", "school_grade",
                  "seo_title", "seo_description", "instant_delivery", "brand", "category",
                  "rating_average", "rating_count", "variants")

    def get_image(self, obj) -> str:
        if obj.image:
            return urljoin(f"{settings.PUBLIC_BASE_URL}/", obj.image.url.lstrip("/"))
        artwork_path = reverse("product-artwork", kwargs={"slug": obj.slug})
        return urljoin(f"{settings.PUBLIC_BASE_URL}/", artwork_path.lstrip("/"))
