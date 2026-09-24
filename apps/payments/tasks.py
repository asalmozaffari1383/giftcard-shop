from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import PaymentTransaction
from .services import fail_stale_payment


@shared_task(acks_late=True, reject_on_worker_lost=True)
def expire_stale_payment_attempts():
    """Fail gateway requests left INITIATING for more than five minutes."""
    stale_before = timezone.now() - timedelta(minutes=5)
    payment_ids = list(PaymentTransaction.objects.filter(
        status=PaymentTransaction.Status.INITIATING,
        created_at__lte=stale_before,
    ).values_list("pk", flat=True)[:500])
    for payment_id in payment_ids:
        fail_stale_payment(payment_id, stale_before)
