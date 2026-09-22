from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    search_fields = ("product__title_fa", "user__phone_number")
    readonly_fields = ("product", "user", "rating", "body")
    actions = ("approve", "reject")

    def has_add_permission(self, request):
        return False

    @admin.action(description="تایید نظرات")
    def approve(self, request, queryset):
        queryset.update(status=Review.Status.APPROVED)

    @admin.action(description="رد نظرات")
    def reject(self, request, queryset):
        queryset.update(status=Review.Status.REJECTED)
