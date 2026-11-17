from django.conf import settings
from django.http import JsonResponse


class CatalogOnlyMiddleware:
    """Publish the catalog without enabling customer accounts or transactions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.CATALOG_ONLY and request.path.startswith("/api/v1/"):
            catalog_read = (
                request.path.startswith("/api/v1/catalog/")
                and request.method in {"GET", "HEAD", "OPTIONS"}
            )
            if not catalog_read:
                return JsonResponse(
                    {"detail": "فروشگاه در حال آماده‌سازی است؛ ورود و ثبت سفارش به‌زودی فعال می‌شود."},
                    status=503,
                )
        return self.get_response(request)
