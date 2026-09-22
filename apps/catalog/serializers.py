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
    stock = serializers.IntegerField(read_only=True)
    price_rial = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ("id", "sku", "label", "face_value", "currency", "region",
                  "price_toman", "price_rial", "old_price_toman", "stock")

    def get_price_rial(self, obj) -> int:
        return obj.price_toman * 10


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ("id", "sku", "title_fa", "slug", "description", "image", "seo_title",
                  "seo_description", "instant_delivery", "brand", "category", "variants")
