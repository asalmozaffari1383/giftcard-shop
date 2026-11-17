from django.db import models

from apps.common.models import TimeStampedModel


class Ticket(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "باز"
        WAITING = "WAITING", "در انتظار پاسخ"
        CLOSED = "CLOSED", "بسته"

    user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="tickets")
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OPEN)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["status", "-updated_at"])]


class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey("users.User", on_delete=models.PROTECT)
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class Inquiry(TimeStampedModel):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=13)
    body = models.TextField(max_length=3000)
    handled = models.BooleanField(default=False)


class SchoolList(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="school_lists")
    title = models.CharField(max_length=200)
    notes = models.TextField(max_length=2000, blank=True)
    file_content = models.BinaryField()
    file_type = models.CharField(max_length=30)
    status = models.CharField(max_length=10, choices=[("PENDING", "در انتظار قیمت‌گذاری"), ("QUOTED", "قیمت‌گذاری‌شده"), ("CLOSED", "بسته‌شده")], default="PENDING")
    quoted_total = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="قیمت پیشنهادی به تومان")
    admin_reply = models.TextField(max_length=3000, blank=True, verbose_name="پاسخ و اقلام پیشنهادی")

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.status == "QUOTED" and (not self.quoted_total or not self.admin_reply.strip()):
            raise ValidationError("برای قیمت‌گذاری، مبلغ مثبت و پاسخ به مشتری را ثبت کنید.")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "لیست مدرسه"
        verbose_name_plural = "لیست‌های مدرسه"
