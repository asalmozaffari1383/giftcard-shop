from datetime import timedelta

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from apps.catalog.models import Product
from apps.orders.models import Order
from .admin import AdminRoleRequiredMixin


def sales_dashboard(request):
    if not AdminRoleRequiredMixin._has_admin_role(request):
        raise PermissionDenied
    now = timezone.now()
    paid = Order.objects.filter(paid_at__isnull=False).exclude(status=Order.Status.REFUNDED)
    daily = list(paid.filter(paid_at__gte=now - timedelta(days=30)).annotate(period=TruncDate("paid_at")).values(
        "period").annotate(total=Sum("total_toman"), count=Count("id")).order_by("period"))
    monthly = list(paid.filter(paid_at__gte=now - timedelta(days=365)).annotate(period=TruncMonth("paid_at")).values(
        "period").annotate(total=Sum("total_toman"), count=Count("id")).order_by("period"))
    for rows in (daily, monthly):
        maximum = max([row["total"] for row in rows], default=1)
        for row in rows:
            row["height"] = max(3, round(row["total"] / maximum * 150))
    customers = paid.values("user_id").annotate(purchases=Count("id"))
    customer_count = customers.count()
    returning = customers.filter(purchases__gt=1).count()
    context = {**admin.site.each_context(request), "title": "داشبورد فروش آلیسان",
               "total_sales": paid.aggregate(total=Sum("total_toman"))["total"] or 0,
               "order_count": paid.count(), "return_rate": round(returning * 100 / customer_count, 1) if customer_count else 0,
               "daily": daily, "monthly": monthly,
               "low_stock": Product.objects.filter(is_active=True, kind="PHYSICAL", stock__lte=5).order_by("stock")[:30]}
    return render(request, "admin/sales_dashboard.html", context)
