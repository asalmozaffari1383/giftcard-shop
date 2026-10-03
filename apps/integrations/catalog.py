import csv
import hashlib
import io
import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import Brand, Category, Product, ProductVariant

from .models import CatalogCandidate, CatalogImportBatch, CatalogSource, normalize_catalog_title

USER_AGENT = "GiftcardShopCatalogResearch/1.0"
REQUEST_TIMEOUT = (5, 25)

BRAND_RULES = (
    (("playstation", "پلی استیشن", "psn", "ps4", "ps5"), "PlayStation"),
    (("xbox", "ایکس باکس", "game pass", "گیم پس"), "Xbox"),
    (("steam", "استیم"), "Steam"),
    (("apple", "اپل", "itunes", "آیتونز"), "Apple"),
    (("google play", "گوگل پلی"), "Google Play"),
    (("spotify", "اسپاتیفای"), "Spotify"),
    (("netflix", "نتفلیکس"), "Netflix"),
    (("telegram", "تلگرام"), "Telegram"),
    (("chatgpt", "openai", "چت جی پی تی"), "OpenAI"),
    (("claude", "کلاد"), "Claude"),
    (("gemini", "جمینی"), "Gemini"),
    (("amazon", "آمازون"), "Amazon"),
    (("nintendo", "نینتندو"), "Nintendo"),
    (("roblox", "روبلاکس"), "Roblox"),
    (("razer", "ریزر"), "Razer"),
    (("pubg", "پابجی"), "PUBG"),
    (("free fire", "فری فایر"), "Free Fire"),
    (("discord", "دیسکورد"), "Discord"),
    (("youtube", "یوتیوب"), "YouTube"),
    (("canva", "کانوا"), "Canva"),
    (("microsoft", "مایکروسافت"), "Microsoft"),
    (("adobe", "ادوبی"), "Adobe"),
)

CATEGORY_RULES = (
    (("گیفت کارت", "gift card", "giftcard"), "گیفت کارت", "gift-cards"),
    (("اکانت بازی", "اکانت قانونی", "ظرفیت", "game account"), "اکانت بازی", "game-accounts"),
    (("الماس", "جم ", "coin", "سکه", "uc ", "کردیت", "شارژ بازی"), "ارز و آیتم بازی", "game-currency"),
    (("اشتراک", "پرمیوم", "premium", "subscription", "اکانت"), "اشتراک و اکانت", "subscriptions"),
)

REGION_RULES = (
    (("آمریکا", "usa", " us "), ProductVariant.Region.US),
    (("ترکیه", "turkey", " tr "), ProductVariant.Region.TR),
    (("امارات", "uae"), ProductVariant.Region.UAE),
)

CURRENCY_RULES = (
    (("دلار", "usd", "$"), "USD"),
    (("یورو", "eur", "€"), "EUR"),
    (("پوند", "gbp", "£"), "GBP"),
    (("لیر", "try"), "TRY"),
    (("درهم", "aed"), "AED"),
)


CURATED_PRODUCTS = {
    "kifpool": [
        "گیفت کارت اپل آیتونز", "گیفت کارت استیم", "گیفت کارت ایکس باکس",
        "گیفت کارت پلی استیشن", "گیفت کارت مایکروسافت", "گیفت کارت ریزر گلد",
        "گیفت کارت اسپاتیفای", "گیفت کارت اسکایپ", "گیفت کارت روبلاکس",
        "گیفت کارت لیگ آف لجندز",
    ],
    "mobogift": [
        "گیفت کارت اپل آیتونز", "گیفت کارت پلی استیشن", "اشتراک پلی استیشن پلاس",
        "گیفت کارت استیم", "گیفت کارت گوگل پلی", "گیفت کارت ایکس باکس",
        "تلگرام پرمیوم", "استارز تلگرام", "اکانت چت جی پی تی پلاس",
        "اکانت‌های پرمیوم هوش مصنوعی", "اشتراک ایکس باکس Core", "گیم پس ایکس باکس",
        "گیفت کارت نینتندو", "گیفت کارت ریزر گلد", "گیفت کارت پابجی موبایل",
        "گیفت کارت روبلاکس", "گیفت کارت آمازون", "اشتراک رادیو جوان",
        "اشتراک اسپاتیفای", "اشتراک اپل موزیک", "اشتراک نتفلیکس", "گیفت کارت هواوی",
        "مستر کارت مجازی", "ویزا کارت مجازی", "گیفت کارت بتل نت", "گیفت کارت فری فایر",
        "گیفت کارت ولورانت", "اشتراک EA Play",
    ],
}


SOURCE_DEFINITIONS = (
    {"name": "کیف پول من", "slug": "kifpool", "base_url": "https://kifpool.me",
     "kind": CatalogSource.Kind.CURATED},
    {"name": "موبوگیفت", "slug": "mobogift", "base_url": "https://mobogift.com",
     "kind": CatalogSource.Kind.CURATED},
    {"name": "Accsell", "slug": "accsell", "base_url": "https://accsell.ir",
     "kind": CatalogSource.Kind.SITEMAP,
     "configuration": {"sitemap": "https://accsell.ir/sitemap1.xml.gz", "product_prefix": "/product/"}},
    {"name": "AccountPlus", "slug": "accountplus", "base_url": "https://accountplus.ir",
     "kind": CatalogSource.Kind.SITEMAP,
     "configuration": {"sitemap": "https://accountplus.ir/sitemap1.xml.gz", "product_prefix": "/product/"}},
    {"name": "آی‌پینز", "slug": "ipinz", "base_url": "https://ipinz.ir",
     "kind": CatalogSource.Kind.SITEMAP,
     "configuration": {"sitemap": "https://ipinz.ir/sitemap.xml", "excluded_paths": ["/", "/products", "/about-us", "/contact-us", "/shopping-flow", "/terms-and-conditions"]}},
    {"name": "نخل مارکت", "slug": "nakhlmarket", "base_url": "https://nakhlmarket.com",
     "kind": CatalogSource.Kind.WOOCOMMERCE,
     "configuration": {"category_ids": [2800]}},
    {"name": "یانگ سنتر", "slug": "yungcenter", "base_url": "https://yungcenter.com",
     "kind": CatalogSource.Kind.WOOCOMMERCE,
     "configuration": {"category_ids": [1095]}},
)


@dataclass(frozen=True)
class CandidateData:
    external_id: str
    source_url: str
    title: str
    image_url: str = ""
    source_sku: str = ""
    source_price: int | None = None
    source_old_price: int | None = None
    source_currency: str = ""
    availability: str = CatalogCandidate.Availability.UNKNOWN
    raw_data: dict | None = None


def normalize_title(value):
    """Backward-compatible alias for the model-level normalizer."""
    return normalize_catalog_title(value)


def classify_product(title):
    """Infer brand, category, region and face value from a public title."""
    normalized = f" {normalize_title(title)} "
    brand = next((label for needles, label in BRAND_RULES
                  if any(needle in normalized for needle in needles)), "محصول دیجیتال")
    category_title, category_slug = "محصولات دیجیتال", "digital-products"
    for needles, label, slug in CATEGORY_RULES:
        if any(needle in normalized for needle in needles):
            category_title, category_slug = label, slug
            break
    region = next((value for needles, value in REGION_RULES
                   if any(needle in normalized for needle in needles)), ProductVariant.Region.GLOBAL)
    currency = next((value for needles, value in CURRENCY_RULES
                     if any(needle in normalized for needle in needles)), "USD")
    latin = str(title).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    amount_match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)(?=\s*(?:دلار|یورو|پوند|لیر|درهم|usd|eur|gbp|try|aed|\$|€|£))",
        latin, flags=re.IGNORECASE,
    )
    face_value = Decimal(amount_match.group(1).replace(",", "")) if amount_match else Decimal("0")
    return {
        "brand": brand, "category_title": category_title, "category_slug": category_slug,
        "region": region, "currency": currency, "face_value": face_value,
    }


def generated_description(candidate, variant_labels):
    """Create original factual copy without copying a competitor description."""
    metadata = classify_product(candidate.title)
    lines = [
        f"{candidate.title} یک محصول دیجیتال در دسته {metadata['category_title']} است.",
        "قیمت نمایش‌داده‌شده آخرین قیمت عمومی ثبت‌شده است و موجودی قابل خرید فقط بر اساس انبار خود فروشگاه تعیین می‌شود.",
    ]
    if variant_labels:
        lines.append(f"گزینه‌های ثبت‌شده: {'، '.join(variant_labels[:8])}.")
    lines.append("پیش از خرید، ریجن و سازگاری محصول با حساب کاربری خود را بررسی کنید.")
    return "\n\n".join(lines)


def ensure_sources():
    sources = []
    for definition in SOURCE_DEFINITIONS:
        defaults = {key: value for key, value in definition.items() if key not in {"slug"}}
        source, _ = CatalogSource.objects.update_or_create(slug=definition["slug"], defaults=defaults)
        sources.append(source)
    return sources


def _request(session, url):
    response = session.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response


def _slug_title(url):
    slug = unquote(urlparse(url).path.strip("/").split("/")[-1])
    return re.sub(r"[-_]+", " ", slug).strip()


def curated_candidates(source):
    for title in CURATED_PRODUCTS[source.slug]:
        external_id = slugify(title, allow_unicode=True)
        yield CandidateData(external_id=external_id, source_url=source.base_url, title=title)


def sitemap_candidates(source, session):
    response = _request(session, source.configuration["sitemap"])
    root = ElementTree.fromstring(response.content)
    excluded = set(source.configuration.get("excluded_paths", []))
    prefix = source.configuration.get("product_prefix")
    for node in root:
        values = {child.tag.rsplit("}", 1)[-1]: child for child in node}
        location_node = values.get("loc")
        if location_node is None or not location_node.text:
            continue
        url = location_node.text.strip()
        path = urlparse(url).path.rstrip("/") or "/"
        if path in excluded or (prefix and not path.startswith(prefix)):
            continue
        title = ""
        image_url = ""
        for child in node.iter():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "title" and child.text and not title:
                title = child.text.strip()
            elif tag == "loc" and child is not location_node and child.text and not image_url:
                image_url = child.text.strip()
        yield CandidateData(external_id=path, source_url=url, title=title or _slug_title(url),
                            image_url=image_url)


def _minor_price(value, minor_unit):
    if value in (None, ""):
        return None
    try:
        return int(Decimal(str(value)) / (Decimal(10) ** int(minor_unit)))
    except (InvalidOperation, ValueError, TypeError):
        return None


def woocommerce_candidates(source, session):
    endpoint = f"{source.base_url}/wp-json/wc/store/v1/products"
    for category_id in source.configuration.get("category_ids", []):
        page = 1
        while True:
            response = _request(session, endpoint + f"?category={category_id}&per_page=100&page={page}")
            products = response.json()
            if not products:
                break
            for product in products:
                prices = product.get("prices") or {}
                minor_unit = prices.get("currency_minor_unit", 0)
                images = product.get("images") or []
                stock_status = product.get("is_in_stock")
                availability = (CatalogCandidate.Availability.IN_STOCK if stock_status is True else
                                CatalogCandidate.Availability.OUT_OF_STOCK if stock_status is False else
                                CatalogCandidate.Availability.UNKNOWN)
                yield CandidateData(
                    external_id=str(product["id"]), source_url=product.get("permalink") or source.base_url,
                    title=product.get("name") or f"محصول {product['id']}",
                    image_url=images[0].get("src", "") if images else "", source_sku=product.get("sku", ""),
                    source_price=_minor_price(prices.get("price"), minor_unit),
                    source_old_price=_minor_price(prices.get("regular_price"), minor_unit),
                    source_currency=prices.get("currency_code", ""), availability=availability,
                    raw_data={"category_id": category_id, "average_rating": product.get("average_rating")},
                )
            total_pages = int(response.headers.get("X-WP-TotalPages", "1"))
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.15)


def source_candidates(source, session=None):
    if session is None:
        import requests

        session = requests.Session()
    if source.kind == CatalogSource.Kind.CURATED:
        return curated_candidates(source)
    if source.kind == CatalogSource.Kind.SITEMAP:
        return sitemap_candidates(source, session)
    if source.kind == CatalogSource.Kind.WOOCOMMERCE:
        return woocommerce_candidates(source, session)
    raise ValueError(f"Unsupported source kind: {source.kind}")


def upsert_candidates(source, candidates, batch=None):
    now = timezone.now()
    created_count = 0
    updated_count = 0
    discovered_count = 0
    with transaction.atomic():
        for candidate in candidates:
            discovered_count += 1
            defaults = {
                "batch": batch, "source_url": candidate.source_url, "source_sku": candidate.source_sku,
                "title": candidate.title[:500], "normalized_title": normalize_title(candidate.title),
                "image_url": candidate.image_url, "source_price": candidate.source_price,
                "source_old_price": candidate.source_old_price, "source_currency": candidate.source_currency,
                "availability": candidate.availability, "raw_data": candidate.raw_data or {},
                "last_seen_at": now,
            }
            _, created = CatalogCandidate.objects.update_or_create(
                source=source, external_id=candidate.external_id[:255], defaults=defaults)
            created_count += int(created)
            updated_count += int(not created)
    return discovered_count, created_count, updated_count


def sync_source(source):
    batch = CatalogImportBatch.objects.create(source=source)
    try:
        counts = upsert_candidates(source, source_candidates(source), batch=batch)
        batch.discovered_count, batch.created_count, batch.updated_count = counts
        batch.status = CatalogImportBatch.Status.COMPLETED
        batch.finished_at = timezone.now()
        batch.save(update_fields=("discovered_count", "created_count", "updated_count", "status",
                                  "finished_at", "updated_at"))
        source.last_synced_at = batch.finished_at
        source.save(update_fields=("last_synced_at", "updated_at"))
        return batch
    except Exception as exc:
        batch.status = CatalogImportBatch.Status.FAILED
        batch.error_count = 1
        batch.error_message = str(exc)[:2000]
        batch.finished_at = timezone.now()
        batch.save(update_fields=("status", "error_count", "error_message", "finished_at", "updated_at"))
        raise


def parse_uploaded_catalog(uploaded_file, filename):
    text = uploaded_file.read().decode("utf-8-sig")
    if filename.lower().endswith(".json"):
        payload = json.loads(text)
        rows = payload.get("products", []) if isinstance(payload, dict) else payload
    elif filename.lower().endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(text)))
    else:
        raise ValueError("فقط فایل JSON یا CSV قابل قبول است.")
    for index, row in enumerate(rows, start=1):
        title = str(row.get("title") or "").strip()
        if not title:
            raise ValueError(f"عنوان محصول در ردیف {index} خالی است.")
        source_url = str(row.get("source_url") or row.get("url") or "").strip()
        if not source_url:
            raise ValueError(f"آدرس منبع در ردیف {index} خالی است.")
        external_id = str(row.get("external_id") or hashlib.sha256(source_url.encode()).hexdigest())
        yield CandidateData(
            external_id=external_id, source_url=source_url, title=title,
            image_url=str(row.get("image_url") or ""), source_sku=str(row.get("sku") or ""),
            source_price=int(row["price"]) if row.get("price") else None,
            source_old_price=int(row["old_price"]) if row.get("old_price") else None,
            source_currency=str(row.get("currency") or ""),
            availability=str(row.get("availability") or CatalogCandidate.Availability.UNKNOWN), raw_data=row,
        )


def _unique_slug(model, seed, fallback):
    base = slugify(seed, allow_unicode=True)[:45] or fallback
    slug = base
    counter = 2
    while model.objects.filter(slug=slug).exists():
        slug = f"{base[:40]}-{counter}"
        counter += 1
    return slug


def _variant_label(data, fallback):
    attributes = data.get("attributes") or data.get("product_attributes") or []
    parts = [str(item.get("value", "")).strip() for item in attributes if item.get("value")]
    return " - ".join(parts)[:120] or str(data.get("label") or data.get("title") or fallback)[:120]


def _candidate_variants(candidate):
    variants = []
    for index, item in enumerate(candidate.raw_data.get("variants") or [], start=1):
        price = item.get("price_toman") or item.get("price")
        if not price:
            continue
        variants.append({
            "sku": str(item.get("sku") or f"{candidate.source_sku}-{index}").strip(),
            "label": _variant_label(item, candidate.title),
            "price_toman": int(price),
            "old_price_toman": item.get("old_price_toman"),
        })
    if not variants and candidate.source_price:
        old_price = candidate.source_old_price
        if old_price is not None and old_price <= candidate.source_price:
            old_price = None
        variants.append({
            "sku": candidate.source_sku,
            "label": "گزینه اصلی",
            "price_toman": candidate.source_price,
            "old_price_toman": old_price,
        })
    return variants


@transaction.atomic
def publish_candidate(candidate, activate=False):
    """Create or update a product while leaving sellable inventory untouched."""
    candidate = CatalogCandidate.objects.select_for_update().select_related("source").get(pk=candidate.pk)
    matched_candidate = CatalogCandidate.objects.filter(
        normalized_title=candidate.normalized_title,
        matched_product__isnull=False,
    ).exclude(pk=candidate.pk).select_related("matched_product").first()
    existing = candidate.matched_product or (matched_candidate.matched_product if matched_candidate else None)
    existing = existing or Product.objects.filter(title_fa=candidate.title).first()
    metadata = classify_product(candidate.title)
    category, _ = Category.objects.get_or_create(
        slug=metadata["category_slug"],
        defaults={"title_fa": metadata["category_title"], "is_active": True},
    )
    brand_slug = slugify(metadata["brand"], allow_unicode=True) or "digital-product"
    brand, _ = Brand.objects.get_or_create(
        slug=brand_slug, defaults={"title_fa": metadata["brand"], "is_active": True})
    variant_data = _candidate_variants(candidate)
    description = generated_description(candidate, [item["label"] for item in variant_data])
    if existing:
        product = existing
        product.category = category
        product.brand = brand
        product.description = description
        product.seo_title = candidate.title[:255]
        product.seo_description = description.replace("\n", " ")[:500]
        product.is_active = product.is_active or activate
        product.save(update_fields=("category", "brand", "description", "seo_title", "seo_description",
                                    "is_active", "updated_at"))
    else:
        digest = hashlib.sha256(f"{candidate.source_id}:{candidate.external_id}".encode()).hexdigest()[:12]
        product = Product.objects.create(
            category=category, brand=brand, sku=f"EXT-{digest.upper()}", title_fa=candidate.title,
            slug=_unique_slug(Product, candidate.title, f"product-{digest}"),
            description=description, seo_title=candidate.title[:255],
            seo_description=description.replace("\n", " ")[:500],
            instant_delivery=True, is_active=activate,
        )
    for index, item in enumerate(variant_data, start=1):
        sku = item["sku"][:64] or f"{product.sku}-{index}"
        if ProductVariant.objects.exclude(product=product).filter(sku=sku).exists():
            sku = f"{product.sku}-{index}"
        ProductVariant.objects.update_or_create(
            product=product,
            sku=sku,
            defaults={
                "label": item["label"], "face_value": metadata["face_value"],
                "currency": metadata["currency"], "region": metadata["region"],
                "price_toman": max(int(item["price_toman"]), 1),
                "old_price_toman": item.get("old_price_toman"), "is_active": activate,
            },
        )
    candidate.matched_product = product
    candidate.review_status = CatalogCandidate.ReviewStatus.IMPORTED
    candidate.save(update_fields=("matched_product", "review_status", "updated_at"))
    return product
