from django.contrib import admin

from .models import Brand, Category, Product, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title_fa", "slug")
    prepopulated_fields = {"slug": ("title_fa",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("title_fa", "is_active")
    search_fields = ("title_fa", "slug")


class VariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "title_fa", "brand", "category", "is_active")
    list_filter = ("is_active", "category", "brand")
    search_fields = ("sku", "title_fa", "slug")
    inlines = (VariantInline,)


@admin.register(ProductVariant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "region", "price_toman", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("sku", "product__title_fa")
