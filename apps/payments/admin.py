from django.contrib import admin
from django.utils.html import format_html

from apps.common.admin import AdminRoleRequiredMixin

from .models import PaymentEvent, PaymentRefund, PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("short_id", "order", "gateway", "formatted_amount", "status_badge", "reference_id", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("id", "order__id", "reference_id")
    readonly_fields = ("order", "gateway", "idempotency_key", "authority", "reference_id",
                       "amount_toman", "status", "verified_at", "created_at")
    date_hierarchy = "created_at"
    list_select_related = ("order", "order__user")

    @admin.display(description="تراکنش")
    def short_id(self, obj): return f"#{str(obj.pk)[:8].upper()}"

    @admin.display(description="مبلغ", ordering="amount_toman")
    def formatted_amount(self, obj): return f"{obj.amount_toman:,} تومان"

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        colors = {"VERIFIED": "#087f5b", "READY": "#b26a00", "INITIATING": "#5f3dc4",
                  "FAILED": "#c92a2a", "RECONCILIATION": "#d9480f"}
        return format_html('<b style="color:{}">{}</b>', colors.get(obj.status, "#444"), obj.get_status_display())

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("payment", "event", "gateway_code", "created_at")
    readonly_fields = ("payment", "event", "gateway_code", "created_at")
    search_fields = ("payment__id", "event")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentRefund)
class PaymentRefundAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("payment", "external_reference", "recorded_by", "created_at")
    readonly_fields = ("payment", "external_reference", "recorded_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
