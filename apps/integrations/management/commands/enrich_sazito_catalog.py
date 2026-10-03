import json
import time

import requests
from django.core.management.base import BaseCommand

from apps.integrations.models import CatalogCandidate


def parse_preloaded_state(html):
    marker = "window.__PRELOADED_STATE__ = JSON.parse('"
    start = html.index(marker) + len(marker)
    end = html.index("')", start)
    escaped = html[start:end].replace("\\'", "'")
    decoded = json.loads('"' + escaped.replace('"', '\\"') + '"')
    return json.loads(decoded)


def extract_product(html):
    product = parse_preloaded_state(html)["entity_route"]["other_props"]
    variants = []
    for variant in product.get("product_variants") or []:
        if not variant.get("enabled") or not variant.get("price"):
            continue
        variants.append({
            "sku": variant.get("sku", ""), "title": variant.get("title", ""),
            "price_toman": int(variant["price"]),
            "attributes": variant.get("product_attributes") or [],
        })
    images = product.get("images") or []
    return {
        "title": product.get("name", ""),
        "sku": variants[0].get("sku", "") if variants else "",
        "price": min((item["price_toman"] for item in variants), default=None),
        "image_url": images[0].get("url", "") if images else "",
        "variants": variants, "product_type": product.get("product_type", "digital"),
    }


class Command(BaseCommand):
    help = "Enrich Sazito candidates with public variants and prices."

    def add_arguments(self, parser):
        parser.add_argument("--delay", type=float, default=0.15)

    def handle(self, *args, **options):
        session = requests.Session()
        session.headers["User-Agent"] = "GiftcardShopCatalogResearch/1.0"
        queryset = CatalogCandidate.objects.filter(source__slug__in=("accsell", "accountplus"))
        updated = failed = 0
        for candidate in queryset.iterator():
            try:
                response = session.get(candidate.source_url, timeout=(5, 30))
                response.raise_for_status()
                data = extract_product(response.text)
                candidate.title = data["title"] or candidate.title
                candidate.source_sku = data["sku"]
                candidate.source_price = data["price"]
                candidate.source_currency = "IRT"
                candidate.image_url = data["image_url"] or candidate.image_url
                candidate.availability = (CatalogCandidate.Availability.IN_STOCK if data["variants"]
                                          else CatalogCandidate.Availability.OUT_OF_STOCK)
                candidate.raw_data = {**candidate.raw_data, **data}
                candidate.save()
                updated += 1
            except (ValueError, KeyError, requests.RequestException) as exc:
                failed += 1
                self.stderr.write(f"{candidate.source_url}: {exc}")
            time.sleep(max(options["delay"], 0))
        self.stdout.write(self.style.SUCCESS(f"updated={updated} failed={failed}"))
