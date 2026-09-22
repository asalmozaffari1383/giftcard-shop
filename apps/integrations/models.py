from django.db import models

from apps.common.models import TimeStampedModel


class FeedSyncLog(TimeStampedModel):
    """Aggregate feed access metadata, never store feed credentials."""

    partner = models.CharField(max_length=30, default="torob")
    page = models.PositiveIntegerField()
    product_count = models.PositiveIntegerField()
