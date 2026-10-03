from django.contrib import admin
from django.db.models import Count, Q

from apps.common.admin import AdminRoleRequiredMixin

from .models import Brand, Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("title_fa", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title_fa", "slug")
    prepopulated_fields = {"slug": ("title_fa",)}


@admin.register(Brand)
class BrandAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("title_fa", "is_active")
    search_fields = ("title_fa", "slug")


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("sku", "title_fa", "brand", "category", "variant_count", "available_stock", "is_active")
    list_filter = ("is_active", "instant_delivery", "category", "brand")
    search_fields = ("sku", "title_fa", "slug")
    inlines = (VariantInline,)
    list_select_related = ("brand", "category")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _variant_count=Count("variants", distinct=True),
            _available_stock=Count("variants__digital_items", filter=Q(variants__digital_items__status="AVAILABLE")),
        )

    @admin.display(description="تنوع‌ها", ordering="_variant_count")
    def variant_count(self, obj): return obj._variant_count

    @admin.display(description="موجودی", ordering="_available_stock")
    def available_stock(self, obj): return obj._available_stock


@admin.register(ProductVariant)
class VariantAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("sku", "product", "label", "region", "formatted_price", "available_stock", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("sku", "product__title_fa")
    list_select_related = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _available_stock=Count("digital_items", filter=Q(digital_items__status="AVAILABLE")))

    @admin.display(description="قیمت", ordering="price_toman")
    def formatted_price(self, obj): return f"{obj.price_toman:,} تومان"

    @admin.display(description="موجودی", ordering="_available_stock")
    def available_stock(self, obj): return obj._available_stock
