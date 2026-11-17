from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

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
    price = models.PositiveBigIntegerField(default=0, verbose_name="قیمت پایه")
    discount = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(99)], verbose_name="تخفیف درصدی")
    kind = models.CharField(max_length=8, choices=[("DIGITAL", "آرشیو دیجیتال"), ("PHYSICAL", "کالای فیزیکی")], default="PHYSICAL")
    age_group = models.CharField(max_length=30, blank=True, verbose_name="رده سنی")
    school_grade = models.CharField(max_length=40, blank=True, verbose_name="پایه تحصیلی")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی")
    images = models.JSONField(default=list, blank=True, verbose_name="تصاویر")
    attributes = models.JSONField(default=dict, blank=True, verbose_name="ویژگی‌ها")
    tags = models.JSONField(default=list, blank=True, verbose_name="برچسب‌ها")
    is_bundle = models.BooleanField(default=False, verbose_name="پک/باندل")
    bundle_items = models.JSONField(default=list, blank=True, verbose_name="اقلام پک")
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)
    instant_delivery = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title_fa

    class Meta:
        indexes = [models.Index(fields=["is_active", "-created_at"])]
        constraints = [models.CheckConstraint(condition=Q(discount__lte=99), name="product_discount_range")]

    def clean(self):
        if not isinstance(self.attributes, dict) or not isinstance(self.tags, list) or not isinstance(self.images, list):
            raise ValidationError("ویژگی‌ها باید شیء و برچسب‌ها و تصاویر باید فهرست باشند.")
        if self.kind == "PHYSICAL" and self.price < 1:
            raise ValidationError({"price": "قیمت کالای فیزیکی باید مثبت باشد."})

    @property
    def final_price(self):
        if self.kind != "PHYSICAL":
            return self.price * (100 - self.discount) // 100
        campaign_discount = getattr(self, "campaign_discount", None)
        if campaign_discount is None:
            now = timezone.now()
            campaign_discount = Campaign.objects.filter(is_active=True, starts_at__lte=now, ends_at__gt=now).filter(
                Q(category_id=self.category_id) | Q(category__isnull=True)).order_by("-percent_off").values_list(
                "percent_off", flat=True).first() or 0
        return max(1, self.price * (100 - max(self.discount, campaign_discount)) // 100)

    @property
    def available_quantity(self):
        if not self.is_bundle:
            return self.stock
        components = list(self.components.select_related("product"))
        if not components or any(not item.product.is_active or item.product.is_bundle or item.product.kind != "PHYSICAL" for item in components):
            return 0
        return min([self.stock] + [item.product.stock // item.quantity for item in components])


class BundleComponent(models.Model):
    bundle = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="components")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_bundles")
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])

    def clean(self):
        if self.bundle_id == self.product_id or self.product.is_bundle or self.product.kind != "PHYSICAL":
            raise ValidationError("اقلام پک باید کالای فیزیکی مستقل باشند.")
        if not self.bundle.is_bundle:
            raise ValidationError("محصول والد باید پک باشد.")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["bundle", "product"], name="unique_bundle_component"),
                       models.CheckConstraint(condition=Q(quantity__gte=1), name="bundle_quantity_positive")]


class Campaign(TimeStampedModel):
    title = models.CharField(max_length=120, verbose_name="عنوان کمپین")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.PROTECT, verbose_name="دسته‌بندی")
    percent_off = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError("پایان کمپین باید بعد از شروع آن باشد.")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(percent_off__gte=1, percent_off__lte=99), name="campaign_percent_range"),
                       models.CheckConstraint(condition=Q(starts_at__lt=F("ends_at")), name="campaign_dates")]

    def __str__(self):
        return self.title


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
