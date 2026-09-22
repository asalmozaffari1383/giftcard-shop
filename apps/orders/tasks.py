from celery import shared_task
from django.utils import timezone

from .models import Order
from .services import expire_order


@shared_task
def expire_reservations():
    """Scheduled sweep; each order rechecks expiry under a row lock."""
    order_ids = list(Order.objects.filter(status=Order.Status.PENDING, expires_at__lte=timezone.now())
                     .values_list("pk", flat=True)[:500])
    for order_id in order_ids:
        expire_order(order_id)
