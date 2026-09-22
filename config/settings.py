"""Environment-driven settings; never deploy with DEBUG or development secrets."""

import os
from datetime import timedelta
from pathlib import Path

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def required(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"{name} is required")
    return value


SECRET_KEY = os.getenv("SECRET_KEY", "development-only-insecure-secret" if DEBUG else None)
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY is required")
ALLOWED_HOSTS = [host for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin]
CORS_ALLOWED_ORIGINS = [origin for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin]
CORS_ALLOW_CREDENTIALS = False

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "rest_framework_simplejwt.token_blacklist", "corsheaders",
    "django_filters", "drf_spectacular",
    "apps.users", "apps.catalog", "apps.inventory", "apps.orders",
    "apps.payments", "apps.reviews", "apps.support", "apps.integrations",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [],
              "APP_DIRS": True, "OPTIONS": {"context_processors": [
                  "django.template.context_processors.debug", "django.template.context_processors.request",
                  "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "users.User"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql", "NAME": required("POSTGRES_DB"),
    "USER": required("POSTGRES_USER"), "PASSWORD": required("POSTGRES_PASSWORD"),
    "HOST": os.getenv("POSTGRES_HOST", "localhost"), "PORT": os.getenv("POSTGRES_PORT", "5432"),
    "CONN_MAX_AGE": 60, "OPTIONS": {"connect_timeout": 5},
}}
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHES = {"default": {"BACKEND": "django_redis.cache.RedisCache", "LOCATION": REDIS_URL,
                       "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"}}}
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_TIME_LIMIT = 60
CELERY_BEAT_SCHEDULE = {
    "release-expired-reservations": {"task": "apps.orders.tasks.expire_reservations", "schedule": 60.0},
}
REST_FRAMEWORK = {
    "URL_FORMAT_OVERRIDE": None,
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination", "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",
                                "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"),
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.AnonRateThrottle",
                                 "rest_framework.throttling.UserRateThrottle"),
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "120/min", "otp": "10/hour"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
              "REFRESH_TOKEN_LIFETIME": timedelta(days=7), "ROTATE_REFRESH_TOKENS": True,
              "BLACKLIST_AFTER_ROTATION": True,
              "SIGNING_KEY": os.getenv("JWT_SIGNING_KEY", SECRET_KEY)}
SPECTACULAR_SETTINGS = {"TITLE": "Digital Marketplace API", "VERSION": "1.0.0"}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if os.getenv("TRUST_PROXY") == "true" else None
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "false").lower() == "true"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "false").lower() == "true"
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2_500_000

INVENTORY_FERNET_KEYS = [key for key in os.getenv("INVENTORY_FERNET_KEYS", "").split(",") if key]
if not INVENTORY_FERNET_KEYS:
    raise ImproperlyConfigured("INVENTORY_FERNET_KEYS is required (comma-separated Fernet keys)")
try:
    for key in INVENTORY_FERNET_KEYS:
        Fernet(key.encode())
except (ValueError, TypeError) as exc:
    raise ImproperlyConfigured("INVENTORY_FERNET_KEYS contains an invalid Fernet key") from exc
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000" if DEBUG else "").rstrip("/")
if not PUBLIC_BASE_URL:
    raise ImproperlyConfigured("PUBLIC_BASE_URL is required")
if not DEBUG and not PUBLIC_BASE_URL.startswith("https://"):
    raise ImproperlyConfigured("PUBLIC_BASE_URL must use HTTPS in production")
SMS_API_URL = os.getenv("SMS_API_URL", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_TEMPLATE_ID = os.getenv("SMS_TEMPLATE_ID", "")
ZARINPAL_MERCHANT_ID = os.getenv("ZARINPAL_MERCHANT_ID", "")
ZARINPAL_SANDBOX = os.getenv("ZARINPAL_SANDBOX", "false").lower() == "true"
TOROB_FEED_KEY = os.getenv("TOROB_FEED_KEY", "")
