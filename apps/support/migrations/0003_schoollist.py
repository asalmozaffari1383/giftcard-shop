import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("support", "0002_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="SchoolList", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("title", models.CharField(max_length=200)), ("notes", models.TextField(blank=True, max_length=2000)),
        ("file_content", models.BinaryField()), ("file_type", models.CharField(max_length=30)),
        ("status", models.CharField(choices=[("PENDING", "در انتظار قیمت‌گذاری"), ("QUOTED", "قیمت‌گذاری‌شده"), ("CLOSED", "بسته‌شده")], default="PENDING", max_length=10)),
        ("quoted_total", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="قیمت پیشنهادی به تومان")),
        ("admin_reply", models.TextField(blank=True, max_length=3000, verbose_name="پاسخ و اقلام پیشنهادی")),
        ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="school_lists", to=settings.AUTH_USER_MODEL)),
    ], options={"verbose_name": "لیست مدرسه", "verbose_name_plural": "لیست‌های مدرسه", "ordering": ("-created_at",)})]
