from django.contrib import admin

from apps.common.admin import AdminRoleRequiredMixin

from .models import PaymentEvent, PaymentRefund, PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("id", "order", "gateway", "amount_toman", "status", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("id", "order__id", "reference_id")
    readonly_fields = ("order", "gateway", "idempotency_key", "authority", "reference_id",
                       "amount_toman", "status", "verified_at", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("payment", "event", "gateway_code", "created_at")
    readonly_fields = ("payment", "event", "gateway_code", "created_at")
    search_fields = ("payment__id", "event")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentRefund)
class PaymentRefundAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("payment", "external_reference", "recorded_by", "created_at")
    readonly_fields = ("payment", "external_reference", "recorded_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
