from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order, OrderStatusHistory


@receiver(pre_save, sender=Order)
def capture_previous_order_status(sender, instance, **kwargs):
    instance._previous_status = ""
    if instance.pk:
        instance._previous_status = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first() or ""


@receiver(post_save, sender=Order)
def record_order_status(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_status", "")
    if created or previous != instance.status:
        OrderStatusHistory.objects.create(order=instance, previous_status=previous, status=instance.status)
