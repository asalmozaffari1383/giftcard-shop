from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from apps.inventory.models import DigitalItem
from apps.payments.models import PaymentTransaction
from apps.payments.services import fulfill_reconciliation


class Command(BaseCommand):
    help = "Inspect a reconciliation payment and optionally fulfill it using its exact reserved inventory."

    def add_arguments(self, parser):
        parser.add_argument("payment_id")
        parser.add_argument(
            "--fulfill",
            action="store_true",
            help="Deliver only when the verified payment still owns every originally reserved item.",
        )

    def handle(self, *args, **options):
        payment = PaymentTransaction.objects.select_related("order").filter(pk=options["payment_id"]).first()
        if not payment:
            raise CommandError("Payment not found.")
        order = payment.order
        reserved = DigitalItem.objects.filter(reserved_order=order, status=DigitalItem.Status.RESERVED).count()
        required = sum(order.items.values_list("quantity", flat=True))
        self.stdout.write(
            f"payment={payment.pk} status={payment.status} order={order.pk} "
            f"order_status={order.status} reserved={reserved}/{required} reference={payment.reference_id or '-'}"
        )
        if not options["fulfill"]:
            self.stdout.write(self.style.WARNING("Inspection only; use --fulfill after settlement review."))
            return
        try:
            fulfill_reconciliation(payment.pk)
        except ValidationError as exc:
            detail = exc.detail
            raise CommandError(str(detail[0] if isinstance(detail, list) else detail)) from exc
        self.stdout.write(self.style.SUCCESS("Payment fulfilled from its intact reservation."))
