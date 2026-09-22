from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class Review(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار تایید"
        APPROVED = "APPROVED", "تاییدشده"
        REJECTED = "REJECTED", "ردشده"

    user = models.ForeignKey("users.User", on_delete=models.PROTECT)
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.TextField(max_length=2000)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="one_review_per_product")]
        indexes = [models.Index(fields=["product", "status", "-created_at"])]
