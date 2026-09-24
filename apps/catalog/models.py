from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.common.models import TimeStampedModel


class Category(TimeStampedModel):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    title_fa = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, allow_unicode=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title_fa

    class Meta:
        verbose_name_plural = "دسته‌بندی‌ها"


class Brand(TimeStampedModel):
    title_fa = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, allow_unicode=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title_fa


class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    sku = models.CharField(max_length=64, unique=True)
    title_fa = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    instant_delivery = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title_fa

    class Meta:
        indexes = [models.Index(fields=["is_active", "-created_at"])]


class ProductVariant(TimeStampedModel):
    class Region(models.TextChoices):
        US = "US", "آمریکا"
        TR = "TR", "ترکیه"
        UAE = "UAE", "امارات"
        GLOBAL = "GLOBAL", "جهانی"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=120)
    face_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="USD")
    region = models.CharField(max_length=12, choices=Region.choices, default=Region.GLOBAL)
    price_toman = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    old_price_toman = models.PositiveBigIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if (self.old_price_toman is not None and self.price_toman is not None and
                self.old_price_toman <= self.price_toman):
            raise ValidationError({"old_price_toman": "قیمت پیشین باید بیشتر از قیمت فعلی باشد."})

    def __str__(self):
        return f"{self.product} — {self.label} ({self.region})"

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(price_toman__gt=0), name="variant_positive_price"),
            models.CheckConstraint(condition=Q(old_price_toman__isnull=True) |
                                   Q(old_price_toman__gt=F("price_toman")),
                                   name="variant_old_price_gt_current"),
        ]
        indexes = [models.Index(fields=["product", "is_active"])]
