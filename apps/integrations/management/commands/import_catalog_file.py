from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.catalog import ensure_sources, parse_uploaded_catalog, upsert_candidates
from apps.integrations.models import CatalogSource


class Command(BaseCommand):
    help = "Import JSON or CSV products into the admin catalog review queue."

    def add_arguments(self, parser):
        parser.add_argument("file", type=Path)
        parser.add_argument("--source", required=True, help="Configured catalog source slug.")

    def handle(self, *args, **options):
        ensure_sources()
        file_path = options["file"]
        if not file_path.is_file():
            raise CommandError(f"File not found: {file_path}")
        try:
            source = CatalogSource.objects.get(slug=options["source"])
        except CatalogSource.DoesNotExist as exc:
            raise CommandError(f"Unknown source: {options['source']}") from exc
        try:
            with file_path.open("rb") as uploaded:
                candidates = parse_uploaded_catalog(uploaded, file_path.name)
                discovered, created, updated = upsert_candidates(source, candidates)
        except (ValueError, TypeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"{source.slug}: {discovered} processed, {created} created, {updated} updated"))
