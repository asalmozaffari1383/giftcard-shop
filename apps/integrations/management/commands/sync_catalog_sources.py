from django.core.management.base import BaseCommand, CommandError

from apps.integrations.catalog import ensure_sources, sync_source


class Command(BaseCommand):
    help = "Synchronize public digital-product catalogs into the admin review queue."

    def add_arguments(self, parser):
        parser.add_argument("--source", action="append", dest="sources",
                            help="Source slug; may be repeated. Defaults to all active sources.")

    def handle(self, *args, **options):
        sources = ensure_sources()
        requested = set(options["sources"] or [])
        if requested:
            available = {source.slug for source in sources}
            unknown = requested - available
            if unknown:
                raise CommandError(f"Unknown source(s): {', '.join(sorted(unknown))}")
            sources = [source for source in sources if source.slug in requested]
        for source in sources:
            if not source.is_active:
                continue
            self.stdout.write(f"Syncing {source.name}...")
            batch = sync_source(source)
            self.stdout.write(self.style.SUCCESS(
                f"{source.slug}: {batch.discovered_count} discovered, "
                f"{batch.created_count} created, {batch.updated_count} updated"))
