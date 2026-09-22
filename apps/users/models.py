import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


def normalize_phone(value):
    """Canonicalize Iranian mobile numbers, including Persian/Arabic digits."""
    value = str(value).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789"))
    value = re.sub(r"[\s\-()]", "", value)
    if value.startswith("0098"):
        value = "+98" + value[4:]
    elif value.startswith("98"):
        value = "+" + value
    elif value.startswith("09"):
        value = "+98" + value[1:]
    if not re.fullmatch(r"\+989\d{9}", value):
        raise ValidationError("شماره موبایل معتبر نیست.")
    return value


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        user = self.model(phone_number=normalize_phone(phone_number), **extra_fields)
        user.set_password(password) if password else user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.update(is_staff=True, is_superuser=True, is_admin=True, is_verified=True)
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    phone_number = models.CharField(max_length=13, unique=True, verbose_name="شماره موبایل")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_support = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []
    objects = UserManager()

    @property
    def is_customer(self):
        return not (self.is_support or self.is_admin)

    def clean(self):
        super().clean()
        self.phone_number = normalize_phone(self.phone_number)

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"


class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)


class OTPChallenge(models.Model):
    phone_number = models.CharField(max_length=13, db_index=True)
    code_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["phone_number", "created_at"])]
