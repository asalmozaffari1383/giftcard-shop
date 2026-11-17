from django.db.models import Count, Q
from django.contrib import admin
from django import forms
from django.contrib.admin.helpers import ActionForm
from django.db import transaction

from apps.common.admin import AdminRoleRequiredMixin

from .models import Brand, BundleComponent, Campaign, Category, Product, ProductVariant


class LowStockFilter(admin.SimpleListFilter):
    title = "هشدار موجودی"
    parameter_name = "low_stock"

    def lookups(self, request, model_admin):
        return (("low", "۵ عدد یا کمتر"), ("empty", "ناموجود"))

    def queryset(self, request, queryset):
        if self.value() == "low":
            return queryset.filter(kind="PHYSICAL", stock__lte=5)
        if self.value() == "empty":
            return queryset.filter(kind="PHYSICAL", stock=0)
        return queryset


class BundleInline(admin.TabularInline):
    model = BundleComponent
    fk_name = "bundle"
    extra = 0
    autocomplete_fields = ("product",)


class BulkProductActionForm(ActionForm):
    bulk_price = forms.IntegerField(required=False, min_value=1, label="قیمت جدید (تومان)")
    bulk_stock = forms.IntegerField(required=False, min_value=0, label="موجودی قابل فروش جدید")
    bulk_discount = forms.IntegerField(required=False, min_value=0, max_value=99, label="تخفیف جدید (%)")


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
    list_display = ("sku", "title_fa", "brand", "category", "price", "discount", "stock", "is_bundle",
                    "variant_count", "available_stock", "is_active")
    list_editable = ("price", "discount", "stock", "is_bundle", "is_active")
    list_filter = (LowStockFilter, "is_active", "kind", "is_bundle", "category", "brand")
    search_fields = ("sku", "title_fa", "slug")
    inlines = (VariantInline, BundleInline)
    list_select_related = ("brand", "category")
    actions = ("activate_products", "deactivate_products", "bulk_update")
    action_form = BulkProductActionForm

    @admin.action(description="اعمال گروهی قیمت، موجودی و تخفیف واردشده")
    @transaction.atomic
    def bulk_update(self, request, queryset):
        form = BulkProductActionForm(request.POST)
        form.fields["action"].choices = self.get_action_choices(request)
        if not form.is_valid():
            self.message_user(request, "مقادیر تغییر گروهی معتبر نیستند.", level="error")
            return
        updates = {name: form.cleaned_data[f"bulk_{name}"] for name in ("price", "stock", "discount") if form.cleaned_data.get(f"bulk_{name}") is not None}
        if not updates:
            self.message_user(request, "حداقل یک مقدار جدید وارد کنید.", level="error")
            return
        eligible = queryset.filter(kind="PHYSICAL").values_list("pk", flat=True)
        selected = list(Product.objects.filter(pk__in=eligible).select_for_update().order_by("pk").values_list("pk", flat=True))
        Product.objects.filter(pk__in=selected).update(**updates)
        self.message_user(request, f"{len(selected)} محصول فیزیکی به‌روزرسانی شد.")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        product = form.instance
        if product.kind == "PHYSICAL" and not product.variants.filter(is_active=True).exists():
            ProductVariant.objects.get_or_create(sku=f"ALI-{product.pk}-DEFAULT", defaults={"product": product,
                "label": "بسته استاندارد", "face_value": 1, "currency": "IRT", "price_toman": product.final_price})

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _variant_count=Count("variants", distinct=True),
            _available_stock=Count("variants__digital_items", filter=Q(variants__digital_items__status="AVAILABLE")),
        )

    @admin.display(description="تنوع‌ها", ordering="_variant_count")
    def variant_count(self, obj): return obj._variant_count

    @admin.display(description="موجودی", ordering="_available_stock")
    def available_stock(self, obj): return obj.available_quantity if obj.kind == "PHYSICAL" else obj._available_stock

    @admin.action(description="فعال‌سازی محصولات انتخاب‌شده")
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="غیرفعال‌سازی محصولات انتخاب‌شده")
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)


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
    def available_stock(self, obj): return obj.product.available_quantity if obj.product.kind == "PHYSICAL" else obj._available_stock


@admin.register(Campaign)
class CampaignAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("title", "category", "percent_off", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title",)
