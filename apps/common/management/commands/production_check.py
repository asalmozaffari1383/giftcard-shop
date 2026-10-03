import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

PLACEHOLDER_PARTS = ("replace-with", "example.com", "your-provider", "change-me")


def _placeholder(value):
    normalized = str(value or "").strip().lower()
    return not normalized or any(part in normalized for part in PLACEHOLDER_PARTS)


def _https(value):
    return urlparse(value).scheme == "https"


def collect_production_issues(*, live=False):
    """Return blocking deployment errors and non-blocking launch warnings."""
    errors = []
    warnings = []
    if settings.DEBUG:
        errors.append("DEBUG must be false.")
    if _placeholder(settings.SECRET_KEY) or len(settings.SECRET_KEY) < 50:
        errors.append("SECRET_KEY must be a non-placeholder secret of at least 50 characters.")
    jwt_key = settings.SIMPLE_JWT["SIGNING_KEY"]
    if _placeholder(jwt_key) or len(jwt_key) < 50 or jwt_key == settings.SECRET_KEY:
        errors.append("JWT_SIGNING_KEY must be strong and independent from SECRET_KEY.")
    if not _https(settings.PUBLIC_BASE_URL) or not _https(settings.FRONTEND_URL):
        errors.append("PUBLIC_BASE_URL and FRONTEND_URL must use HTTPS.")
    if os.getenv("NEXT_PUBLIC_SITE_URL", "").rstrip("/") != settings.FRONTEND_URL:
        errors.append("NEXT_PUBLIC_SITE_URL must exactly match FRONTEND_URL.")
    if not settings.ALLOWED_HOSTS or any(host in {"*", "localhost", "127.0.0.1"} for host in settings.ALLOWED_HOSTS):
        errors.append("ALLOWED_HOSTS must contain only final deployment hosts.")
    if any(not _https(origin) for origin in settings.CSRF_TRUSTED_ORIGINS):
        errors.append("Every CSRF trusted origin must use HTTPS.")
    if any(not _https(origin) for origin in settings.CORS_ALLOWED_ORIGINS):
        errors.append("Every CORS allowed origin must use HTTPS.")
    if not settings.SESSION_COOKIE_SECURE or not settings.CSRF_COOKIE_SECURE or not settings.SECURE_SSL_REDIRECT:
        errors.append("Secure cookies and HTTPS redirect must be enabled.")
    if settings.SECURE_PROXY_SSL_HEADER is None:
        errors.append("TRUST_PROXY=true is required behind the deployment reverse proxy.")
    if settings.DEVELOPMENT_OTP_CODE:
        errors.append("DEVELOPMENT_OTP_CODE must be empty.")
    if settings.PAYMENT_GATEWAY != "zarinpal":
        errors.append("PAYMENT_GATEWAY must be zarinpal.")
    if _placeholder(settings.ZARINPAL_MERCHANT_ID):
        errors.append("ZARINPAL_MERCHANT_ID is missing or still a placeholder.")
    if live and settings.ZARINPAL_SANDBOX:
        errors.append("ZARINPAL_SANDBOX must be false for a live launch.")
    elif settings.ZARINPAL_SANDBOX:
        warnings.append("Zarinpal sandbox is enabled; suitable for final staging only.")
    if not _https(settings.SMS_API_URL):
        errors.append("SMS_API_URL must be the provider HTTPS endpoint.")
    if (_placeholder(settings.SMS_API_KEY) or _placeholder(settings.SMS_TEMPLATE_ID)
            or _placeholder(settings.SMS_ORDER_TEMPLATE_ID)):
        errors.append("SMS_API_KEY, SMS_TEMPLATE_ID and SMS_ORDER_TEMPLATE_ID must be configured.")
    if _placeholder(os.getenv("POSTGRES_PASSWORD")):
        errors.append("POSTGRES_PASSWORD is missing or still a placeholder.")
    redis_url = settings.REDIS_URL
    if _placeholder(redis_url) or "@" not in redis_url:
        errors.append("REDIS_URL must include production authentication.")
    if os.getenv("AUTH_COOKIE_SECURE", "").lower() != "true":
        errors.append("AUTH_COOKIE_SECURE=true is required for the frontend proxy.")
    if not settings.SECURE_HSTS_INCLUDE_SUBDOMAINS:
        warnings.append("HSTS includeSubDomains is disabled; enable only after every subdomain supports HTTPS.")
    if not settings.SECURE_HSTS_PRELOAD:
        warnings.append("HSTS preload is disabled; enable only after the domain is permanently ready.")
    business_fields = {
        "NEXT_PUBLIC_BUSINESS_NAME": os.getenv("NEXT_PUBLIC_BUSINESS_NAME", ""),
        "NEXT_PUBLIC_SUPPORT_PHONE": os.getenv("NEXT_PUBLIC_SUPPORT_PHONE", ""),
        "NEXT_PUBLIC_SUPPORT_HOURS": os.getenv("NEXT_PUBLIC_SUPPORT_HOURS", ""),
        "NEXT_PUBLIC_BUSINESS_ADDRESS": os.getenv("NEXT_PUBLIC_BUSINESS_ADDRESS", ""),
    }
    missing_business = [name for name, value in business_fields.items() if _placeholder(value)]
    if missing_business:
        errors.append(f"Public legal business fields are incomplete: {', '.join(missing_business)}.")
    enamad_fields = (os.getenv("NEXT_PUBLIC_ENAMAD_URL", ""), os.getenv("NEXT_PUBLIC_ENAMAD_LOGO_URL", ""))
    if any(_placeholder(value) for value in enamad_fields):
        message = "Enamad verification and logo URLs are not configured."
        (errors if live else warnings).append(message)
    if _placeholder(settings.TOROB_FEED_KEY):
        message = "TOROB_FEED_KEY is not configured; the partner feed will remain unavailable."
        (errors if live else warnings).append(message)
    return errors, warnings


class Command(BaseCommand):
    help = "Fail fast when deployment credentials or production security settings are incomplete."

    def add_arguments(self, parser):
        parser.add_argument("--live", action="store_true", help="Also require the live payment gateway mode.")

    def handle(self, *args, **options):
        errors, warnings = collect_production_issues(live=options["live"])
        for warning in warnings:
            self.stdout.write(self.style.WARNING(f"WARNING: {warning}"))
        if errors:
            for error in errors:
                self.stderr.write(self.style.ERROR(f"ERROR: {error}"))
            raise CommandError(f"Production readiness failed with {len(errors)} blocking issue(s).")
        self.stdout.write(self.style.SUCCESS("Production readiness checks passed."))
