from django.core.management.base import BaseCommand

from apps.integrations.catalog import publish_candidate
from apps.integrations.models import CatalogCandidate


class Command(BaseCommand):
    help = "Publish visible products without creating sellable inventory."

    def add_arguments(self, parser):
        parser.add_argument("--source", action="append", dest="sources")

    def handle(self, *args, **options):
        queryset = CatalogCandidate.objects.select_related("source").order_by("id")
        if options["sources"]:
            queryset = queryset.filter(source__slug__in=options["sources"])
        published = 0
        for candidate in queryset.iterator():
            publish_candidate(candidate, activate=True)
            published += 1
        self.stdout.write(self.style.SUCCESS(f"published={published}"))
