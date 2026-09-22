from django.contrib import admin

from .models import Cart, CartItem, Coupon, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("variant", "quantity", "unit_price_toman")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "total_toman", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__phone_number")
    readonly_fields = ("user", "status", "subtotal_toman", "discount_toman", "total_toman",
                       "coupon", "expires_at", "paid_at", "created_at")
    inlines = (OrderItemInline,)

    def has_add_permission(self, request):
        return False


admin.site.register(Coupon)
admin.site.register(Cart)
admin.site.register(CartItem)
