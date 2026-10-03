import re

from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


def normalize_catalog_title(value):
    """Normalize Persian/Arabic characters and spacing for duplicate detection."""
    value = str(value or "").translate(str.maketrans("يكىۀة", "یکیهه"))
    value = re.sub(r"[^\w\u0600-\u06ff]+", " ", value.lower(), flags=re.UNICODE)
    return " ".join(value.split())[:500]


class FeedSyncLog(TimeStampedModel):
    """Aggregate feed access metadata, never store feed credentials."""

    partner = models.CharField(max_length=30, default="torob")
    page = models.PositiveIntegerField()
    product_count = models.PositiveIntegerField()


class CatalogSource(TimeStampedModel):
    """A public catalog used only as a product-discovery source."""

    class Kind(models.TextChoices):
        CURATED = "CURATED", "فهرست عمومی"
        SITEMAP = "SITEMAP", "نقشه سایت"
        WOOCOMMERCE = "WOOCOMMERCE", "ووکامرس"

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    base_url = models.URLField()
    kind = models.CharField(max_length=20, choices=Kind.choices)
    is_active = models.BooleanField(default=True)
    configuration = models.JSONField(default=dict, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class CatalogImportBatch(TimeStampedModel):
    """Audit record for a catalog synchronization or uploaded import file."""

    class Status(models.TextChoices):
        RUNNING = "RUNNING", "در حال اجرا"
        COMPLETED = "COMPLETED", "تکمیل‌شده"
        FAILED = "FAILED", "ناموفق"

    source = models.ForeignKey(CatalogSource, null=True, blank=True, on_delete=models.PROTECT,
                               related_name="batches")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    discovered_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)


class CatalogCandidate(TimeStampedModel):
    """Staged external product; it never becomes sellable without admin approval."""

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", "در انتظار بررسی"
        APPROVED = "APPROVED", "تأییدشده"
        REJECTED = "REJECTED", "ردشده"
        IMPORTED = "IMPORTED", "وارد کاتالوگ شده"

    class Availability(models.TextChoices):
        IN_STOCK = "IN_STOCK", "موجود"
        OUT_OF_STOCK = "OUT_OF_STOCK", "ناموجود"
        UNKNOWN = "UNKNOWN", "نامشخص"

    source = models.ForeignKey(CatalogSource, on_delete=models.PROTECT, related_name="candidates")
    batch = models.ForeignKey(CatalogImportBatch, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="candidates")
    external_id = models.CharField(max_length=255)
    source_url = models.URLField(max_length=1000)
    source_sku = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=500)
    normalized_title = models.CharField(max_length=500, db_index=True, blank=True, editable=False)
    image_url = models.URLField(max_length=1000, blank=True)
    source_price = models.PositiveBigIntegerField(null=True, blank=True)
    source_old_price = models.PositiveBigIntegerField(null=True, blank=True)
    source_currency = models.CharField(max_length=10, blank=True)
    availability = models.CharField(max_length=16, choices=Availability.choices,
                                    default=Availability.UNKNOWN)
    review_status = models.CharField(max_length=12, choices=ReviewStatus.choices,
                                     default=ReviewStatus.PENDING)
    matched_product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="source_candidates")
    raw_data = models.JSONField(default=dict, blank=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("source", "external_id"),
                                                name="catalog_candidate_source_external")]
        indexes = [
            models.Index(fields=("review_status", "-updated_at")),
            models.Index(fields=("source", "availability")),
        ]
        ordering = ("-updated_at",)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.normalized_title = normalize_catalog_title(self.title)
        super().save(*args, **kwargs)
