import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_bundlecomponent_product_age_group_product_kind_and_more")]

    operations = [
        migrations.AlterField(model_name="product", name="kind", field=models.CharField(
            choices=[("DIGITAL", "آرشیو دیجیتال"), ("PHYSICAL", "کالای فیزیکی")], default="PHYSICAL", max_length=8)),
        migrations.CreateModel(name="Campaign", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("title", models.CharField(max_length=120, verbose_name="عنوان کمپین")),
            ("percent_off", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(99)])),
            ("starts_at", models.DateTimeField()), ("ends_at", models.DateTimeField()),
            ("is_active", models.BooleanField(default=True)),
            ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="catalog.category", verbose_name="دسته‌بندی")),
        ], options={"constraints": [
            models.CheckConstraint(condition=models.Q(percent_off__gte=1, percent_off__lte=99), name="campaign_percent_range"),
            models.CheckConstraint(condition=models.Q(starts_at__lt=models.F("ends_at")), name="campaign_dates")]}),
    ]
