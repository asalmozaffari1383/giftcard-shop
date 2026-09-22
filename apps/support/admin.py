from django.contrib import admin

from .models import Inquiry, Ticket, TicketMessage


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subject", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("user__phone_number", "subject")


admin.site.register(TicketMessage)
admin.site.register(Inquiry)
