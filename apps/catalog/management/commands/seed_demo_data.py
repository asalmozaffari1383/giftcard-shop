import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Category, Product, ProductVariant
from apps.inventory.models import DigitalItem


class Command(BaseCommand):
    """Create an idempotent development catalog with encrypted inventory."""

    help = "Create sample catalog and encrypted inventory for local development."

    products = (
        ("گیفت کارت پلی‌استیشن آمریکا", "playstation-us", "PSN", "PlayStation", "playstation", "US",
         (("10 دلار", "10", "USD", 890_000), ("25 دلار", "25", "USD", 2_120_000))),
        ("گیفت کارت استیم جهانی", "steam-global", "STEAM", "Steam", "steam", "GLOBAL",
         (("10 دلار", "10", "USD", 910_000), ("20 دلار", "20", "USD", 1_790_000))),
        ("گیفت کارت اپل آمریکا", "apple-us", "APPLE", "Apple", "apple", "US",
         (("10 دلار", "10", "USD", 940_000), ("25 دلار", "25", "USD", 2_290_000))),
        ("گیفت کارت گوگل پلی آمریکا", "google-play-us", "GOOGLE", "Google Play", "google-play", "US",
         (("10 دلار", "10", "USD", 900_000),)),
        ("گیفت کارت ایکس‌باکس ترکیه", "xbox-tr", "XBOX", "Xbox", "xbox", "TR",
         (("۵۰۰ لیر", "500", "TRY", 1_350_000),)),
        ("اشتراک اسپاتیفای امارات", "spotify-uae", "SPOTIFY", "Spotify", "spotify", "UAE",
         (("یک ماهه", "1", "AED", 420_000), ("سه ماهه", "3", "AED", 1_150_000))),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = Category.objects.update_or_create(
            slug="gift-cards", defaults={"title_fa": "گیفت کارت", "is_active": True})
        created_products = 0
        created_items = 0

        for title, slug, prefix, brand_title, brand_slug, region, variants in self.products:
            brand, _ = Brand.objects.update_or_create(
                slug=brand_slug, defaults={"title_fa": brand_title, "is_active": True})
            product, was_created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": category,
                    "brand": brand,
                    "sku": f"DEMO-{prefix}",
                    "title_fa": title,
                    "description": "محصول نمونه برای بررسی رابط فروشگاه و جریان خرید در محیط توسعه.",
                    "seo_title": title,
                    "seo_description": f"خرید آنلاین {title} با تحویل سریع کد دیجیتال.",
                    "instant_delivery": True,
                    "is_active": True,
                },
            )
            created_products += int(was_created)

            for index, (label, face_value, currency, price) in enumerate(variants, start=1):
                variant, _ = ProductVariant.objects.update_or_create(
                    sku=f"DEMO-{prefix}-{index}",
                    defaults={
                        "product": product,
                        "label": label,
                        "face_value": Decimal(face_value),
                        "currency": currency,
                        "region": region,
                        "price_toman": price,
                        "old_price_toman": None,
                        "is_active": True,
                    },
                )
                available = variant.digital_items.filter(status=DigitalItem.Status.AVAILABLE).count()
                for _ in range(max(0, 5 - available)):
                    item = DigitalItem(variant=variant)
                    item.set_secret(f"DEMO-{prefix}-{uuid.uuid4().hex[:16].upper()}")
                    item.full_clean()
                    item.save()
                    created_items += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demo catalog ready: {created_products} new products, {created_items} new encrypted items."))
