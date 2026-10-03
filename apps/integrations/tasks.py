from celery import shared_task

from .catalog import ensure_sources, sync_source
from .models import CatalogSource


@shared_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_catalog_source(source_id):
    """Synchronize one public source outside the web request cycle."""
    ensure_sources()
    batch = sync_source(CatalogSource.objects.get(pk=source_id, is_active=True))
    return batch.pk
