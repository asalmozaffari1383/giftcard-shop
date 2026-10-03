from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_productvariant_variant_old_price_gt_current"),
        ("integrations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CatalogSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(unique=True)),
                ("base_url", models.URLField()),
                ("kind", models.CharField(choices=[("CURATED", "فهرست عمومی"), ("SITEMAP", "نقشه سایت"), ("WOOCOMMERCE", "ووکامرس")], max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("configuration", models.JSONField(blank=True, default=dict)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="CatalogImportBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("RUNNING", "در حال اجرا"), ("COMPLETED", "تکمیل‌شده"), ("FAILED", "ناموفق")], default="RUNNING", max_length=12)),
                ("discovered_count", models.PositiveIntegerField(default=0)),
                ("created_count", models.PositiveIntegerField(default=0)),
                ("updated_count", models.PositiveIntegerField(default=0)),
                ("error_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("source", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="integrations.catalogsource")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="CatalogCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("external_id", models.CharField(max_length=255)),
                ("source_url", models.URLField(max_length=1000)),
                ("source_sku", models.CharField(blank=True, max_length=100)),
                ("title", models.CharField(max_length=500)),
                ("normalized_title", models.CharField(blank=True, db_index=True, editable=False, max_length=500)),
                ("image_url", models.URLField(blank=True, max_length=1000)),
                ("source_price", models.PositiveBigIntegerField(blank=True, null=True)),
                ("source_old_price", models.PositiveBigIntegerField(blank=True, null=True)),
                ("source_currency", models.CharField(blank=True, max_length=10)),
                ("availability", models.CharField(choices=[("IN_STOCK", "موجود"), ("OUT_OF_STOCK", "ناموجود"), ("UNKNOWN", "نامشخص")], default="UNKNOWN", max_length=16)),
                ("review_status", models.CharField(choices=[("PENDING", "در انتظار بررسی"), ("APPROVED", "تأییدشده"), ("REJECTED", "ردشده"), ("IMPORTED", "وارد کاتالوگ شده")], default="PENDING", max_length=12)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("last_seen_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="candidates", to="integrations.catalogimportbatch")),
                ("matched_product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="source_candidates", to="catalog.product")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="candidates", to="integrations.catalogsource")),
            ],
            options={"ordering": ("-updated_at",)},
        ),
        migrations.AddConstraint(
            model_name="catalogcandidate",
            constraint=models.UniqueConstraint(fields=("source", "external_id"), name="catalog_candidate_source_external"),
        ),
        migrations.AddIndex(
            model_name="catalogcandidate",
            index=models.Index(fields=["review_status", "-updated_at"], name="integration_review__d8f15e_idx"),
        ),
        migrations.AddIndex(
            model_name="catalogcandidate",
            index=models.Index(fields=["source", "availability"], name="integration_source__056465_idx"),
        ),
    ]
