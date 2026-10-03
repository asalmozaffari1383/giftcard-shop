from django.contrib import admin

from apps.common.admin import StaffRoleRequiredMixin

from .models import Inquiry, Ticket, TicketMessage


class TicketMessageInline(admin.StackedInline):
    model = TicketMessage
    extra = 0
    readonly_fields = ("author", "body", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Ticket)
class TicketAdmin(StaffRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("id", "user", "subject", "status", "order", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("user__phone_number", "subject", "order__id", "messages__body")
    readonly_fields = ("user", "subject", "order", "created_at", "updated_at")
    inlines = (TicketMessageInline,)
    date_hierarchy = "created_at"
    list_select_related = ("user", "order")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TicketMessage)
class TicketMessageAdmin(StaffRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("ticket__subject", "ticket__user__phone_number", "body")
    readonly_fields = ("ticket", "author", "body", "created_at")

    def has_add_permission(self, request): return False

    def has_change_permission(self, request, obj=None): return False

    def has_delete_permission(self, request, obj=None): return False


@admin.register(Inquiry)
class InquiryAdmin(StaffRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("name", "phone_number", "handled", "created_at")
    list_filter = ("handled", "created_at")
    search_fields = ("name", "phone_number", "body")
    readonly_fields = ("name", "phone_number", "body", "created_at", "updated_at")
    actions = ("mark_handled",)

    @admin.action(description="علامت‌گذاری به‌عنوان رسیدگی‌شده")
    def mark_handled(self, request, queryset): queryset.update(handled=True)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
