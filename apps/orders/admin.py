from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from apps.common.admin import AdminRoleRequiredMixin

from .models import Cart, CartItem, Coupon, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "quantity", "unit_price_toman")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class OrderHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("previous_status", "status", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("short_id", "user", "status_badge", "item_count", "formatted_total", "created_at")
    list_filter = ("status", "created_at", "paid_at")
    search_fields = ("id", "user__phone_number", "items__variant__sku", "items__variant__product__title_fa")
    readonly_fields = ("id", "user", "status", "subtotal_toman", "discount_toman", "total_toman",
                       "coupon", "expires_at", "paid_at", "idempotency_key", "created_at", "updated_at")
    inlines = (OrderItemInline, OrderHistoryInline)
    date_hierarchy = "created_at"
    list_select_related = ("user", "coupon")
    list_per_page = 30

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_item_count=Count("items"))

    @admin.display(description="سفارش", ordering="id")
    def short_id(self, obj):
        return f"#{str(obj.pk)[:8].upper()}"

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        colors = {"COMPLETED": "#087f5b", "PENDING": "#b26a00", "PROCESSING": "#5f3dc4",
                  "CANCELED": "#6b7280", "FAILED": "#c92a2a", "REFUNDED": "#1971c2"}
        return format_html('<b style="color:{}">{}</b>', colors.get(obj.status, "#444"), obj.get_status_display())

    @admin.display(description="اقلام", ordering="_item_count")
    def item_count(self, obj):
        return obj._item_count

    @admin.display(description="مبلغ نهایی", ordering="total_toman")
    def formatted_total(self, obj):
        return f"{obj.total_toman:,} تومان"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Coupon)
class CouponAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("code", "percent_off", "max_discount_toman", "usage", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("code",)
    readonly_fields = ("used_count", "created_at", "updated_at")
    date_hierarchy = "starts_at"

    @admin.display(description="مصرف")
    def usage(self, obj):
        return f"{obj.used_count:,} / {obj.usage_limit:,}"


@admin.register(Cart)
class CartAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__phone_number",)
    readonly_fields = ("user", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CartItem)
class CartItemAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity")
    search_fields = ("cart__user__phone_number", "variant__sku")
    readonly_fields = ("cart", "variant", "quantity")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
