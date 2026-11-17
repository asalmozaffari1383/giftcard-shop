from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.common.admin import AdminRoleRequiredMixin, StaffRoleRequiredMixin

from .models import Inquiry, SchoolList, Ticket, TicketMessage


@admin.register(SchoolList)
class SchoolListAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("title", "user", "status", "quoted_total", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "user__phone_number")
    readonly_fields = ("user", "title", "notes", "download_file", "created_at", "updated_at")
    exclude = ("file_content", "file_type")

    @admin.display(description="لیست بارگذاری‌شده")
    def download_file(self, obj):
        return format_html('<a href="{}">دریافت فایل لیست مدرسه</a>', reverse("school-list-admin-file", args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
