from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from apps.catalog.models import ProductVariant
from apps.inventory.models import DigitalItem


class Command(BaseCommand):
    help = "Import newline-separated digital secrets for one product variant."

    def add_arguments(self, parser):
        parser.add_argument("--variant-sku", required=True)
        parser.add_argument("--file", required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
            raise CommandError("Input file is missing or larger than 10 MB")
        secrets = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if not secrets:
            raise CommandError("Input file contains no secrets")
        if len(secrets) > 10_000:
            raise CommandError("A single import is limited to 10,000 secrets")
        if len(secrets) != len(set(secrets)):
            raise CommandError("Input file contains duplicate secrets")
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Validated {len(secrets)} secrets"))
            return
        try:
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(sku=options["variant_sku"])
                for plaintext in secrets:
                    item = DigitalItem(variant=variant)
                    item.set_secret(plaintext)
                    item.save()
        except ProductVariant.DoesNotExist as exc:
            raise CommandError("Variant SKU was not found") from exc
        except IntegrityError as exc:
            raise CommandError("One or more secrets already exist in inventory") from exc
        self.stdout.write(self.style.SUCCESS(f"Imported {len(secrets)} encrypted digital items"))
