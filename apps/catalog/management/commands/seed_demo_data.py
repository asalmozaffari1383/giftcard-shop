from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Brand, BundleComponent, Category, Product, ProductVariant
from apps.orders.models import Coupon, ShippingMethod


class Command(BaseCommand):
    """Create an idempotent Persian stationery catalog for local development."""

    help = "Create Alisan stationery catalog and sample stock for local development."

    categories = {
        "notebook": "دفتر و کلاسور", "writing": "نوشت‌افزار", "special": "کتاب و دفترهای مخصوص",
        "school-packs": "بسته‌های مدرسه", "office": "تجهیزات اداری", "gift-sets": "هدیه و ست کادویی",
        "exam-packs": "پک دانشجویی/امتحانی",
    }
    brands = {"kaden": "کادن", "masti": "ماستی", "aysa": "آیسا", "naji": "ناجی"}
    products = (
        ("دفتر سیمی کادن ۱۰۰ برگ", "kaden-notebook-100", "kaden", "notebook", 165_000, 10,
         {"تعداد صفحات": "۱۰۰", "جنس جلد": "مقوایی", "نوع خط‌کشی": "خط‌دار", "سال مدرسه": "۱۴۰۵"}, ["دفتر", "خط‌دار"]),
        ("دفتر کلاسوری ماستی A5", "masti-binder-a5", "masti", "notebook", 285_000, 15,
         {"تعداد صفحات": "۸۰", "جنس جلد": "طلقی", "نوع خط‌کشی": "چهارخانه", "قطع": "A5"}, ["کلاسور", "A5"]),
        ("خودکار ژله‌ای آیسا بسته ۶ عددی", "aysa-gel-pens-6", "aysa", "writing", 195_000, 0,
         {"رنگ": "رنگارنگ", "تعداد": "۶", "قطر نوک": "۰.۷ میلی‌متر"}, ["خودکار", "رنگی"]),
        ("مداد مشکی ناجی بسته ۱۲ عددی", "naji-pencils-12", "naji", "writing", 120_000, 5,
         {"درجه سختی": "HB", "تعداد": "۱۲", "بدنه": "چوبی"}, ["مداد", "مدرسه"]),
        ("جامدادی پارچه‌ای آلیسان", "alisan-pencil-case", "aysa", "gift-sets", 210_000, 0,
         {"جنس": "برزنت", "تعداد محفظه": "۳", "رنگ": "پاستلی"}, ["جامدادی", "هدیه"]),
        ("پک کامل پایه اول دبستان", "school-pack-grade-1", "kaden", "school-packs", 1_490_000, 15,
         {"پایه": "اول دبستان", "اقلام": "دفتر، مداد، پاک‌کن، تراش، جامدادی"}, ["پک مدرسه", "پایه اول"], True,
         ["دفتر سیمی کادن", "مداد مشکی ناجی", "جامدادی پارچه‌ای"]),
        ("پک امتحانی دانشجویی", "student-exam-pack", "masti", "exam-packs", 895_000, 8,
         {"اقلام": "دفتر، خودکار، هایلایتر، برگه یادداشت"}, ["امتحان", "دانشجویی"], True,
         ["دفتر کلاسوری ماستی", "خودکار ژله‌ای آیسا"]),
        ("ست هدیه رنگین آلیسان", "alisan-colorful-gift", "aysa", "gift-sets", 650_000, 12,
         {"اقلام": "دفتر، خودکار، استیکر و کارت هدیه"}, ["هدیه", "ست کادویی"], True,
         ["دفتر سیمی کادن", "خودکار ژله‌ای آیسا"]),
        ("پوشه دکمه‌دار اداری ناجی", "naji-office-folder", "naji", "office", 95_000, 0,
         {"جنس": "پلاستیک مات", "قطع": "A4", "رنگ": "شفاف"}, ["اداری", "پوشه"]),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("داده نمونه فقط در محیط توسعه ساخته می‌شود.")
        category_objects = {slug: Category.objects.update_or_create(
            slug=slug, defaults={"title_fa": title, "is_active": True})[0]
            for slug, title in self.categories.items()}
        Brand.objects.filter(slug__in=["playstation", "steam", "apple", "google-play", "xbox", "spotify"]).update(
            is_active=False)
        brand_objects = {slug: Brand.objects.update_or_create(
            slug=slug, defaults={"title_fa": title, "is_active": True})[0]
            for slug, title in self.brands.items()}
        rows = list(self.products)
        for grade in range(2, 7):
            rows.append((f"پک کامل پایه {grade} دبستان", f"school-pack-grade-{grade}", "kaden", "school-packs", 1_490_000, 15,
                         {"پایه": str(grade), "اقلام": "دفتر، مداد و جامدادی"}, ["پک مدرسه"], True,
                         ["دفتر سیمی کادن", "مداد مشکی ناجی", "جامدادی پارچه‌ای"]))
        slugs = {row[1] for row in rows}
        Product.objects.exclude(slug__in=slugs).update(is_active=False)
        created_products = 0
        created_units = 0
        for row in rows:
            title, slug, brand_slug, category_slug, price, discount, attributes, tags, *extra = row
            is_bundle = bool(extra[0]) if extra else False
            bundle_items = extra[1] if len(extra) > 1 else []
            old_price = price if discount else None
            sale_price = price * (100 - discount) // 100
            previous = Product.objects.filter(slug=slug).first()
            stock = previous.stock if previous and previous.kind == "PHYSICAL" else 12
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": category_objects[category_slug], "brand": brand_objects[brand_slug],
                    "sku": f"STA-{slug.upper()}", "title_fa": title,
                    "description": f"{title} با انتخابی کاربردی و کیفیت مناسب برای خرید از آلیسان.",
                    "seo_title": title, "seo_description": f"خرید {title} از فروشگاه آلیسان.",
                    "price": price, "discount": discount, "attributes": attributes, "tags": tags,
                    "is_bundle": is_bundle, "bundle_items": bundle_items, "stock": stock, "kind": "PHYSICAL",
                    "age_group": "دانشجو" if category_slug == "exam-packs" else "مدرسه",
                    "school_grade": slug.rsplit("-", 1)[-1] if slug.startswith("school-pack-grade-") else "",
                    "instant_delivery": False, "is_active": True,
                },
            )
            created_products += int(created)
            variant, _ = ProductVariant.objects.update_or_create(
                sku=f"STA-{slug.upper()}-ONE",
                defaults={"product": product, "label": "یک عدد / بسته", "face_value": Decimal("1"),
                          "currency": "IRT", "region": "GLOBAL", "price_toman": sale_price,
                          "old_price_toman": old_price, "is_active": True},
            )
            created_units += stock if created else 0
        for product in Product.objects.filter(slug__in=slugs, is_bundle=True):
            component_slugs = ["kaden-notebook-100", "naji-pencils-12", "alisan-pencil-case"] if product.school_grade else (
                ["masti-binder-a5", "aysa-gel-pens-6"] if product.slug == "student-exam-pack" else ["kaden-notebook-100", "aysa-gel-pens-6"])
            for slug in component_slugs:
                BundleComponent.objects.get_or_create(bundle=product, product=Product.objects.get(slug=slug), defaults={"quantity": 1})
        ShippingMethod.objects.get_or_create(title="پست پیشتاز", defaults={"price_toman": 65000, "free_above_toman": 2000000})
        now = timezone.now()
        Coupon.objects.get_or_create(code="ALISAN10", defaults={"percent_off": 10, "usage_limit": 1000,
                                    "starts_at": now, "ends_at": now + timedelta(days=365)})
        self.stdout.write(self.style.SUCCESS(
            f"Alisan stationery catalog ready: {created_products} new products, {created_units} new stock units."))
