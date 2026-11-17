from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.common.dashboard import sales_dashboard
from apps.support.school_lists import admin_school_file

admin.site.site_header = "مدیریت آلیسان"
admin.site.site_title = "پنل مدیریت آلیسان"
admin.site.index_title = "کنترل فروش، سفارش‌ها و موجودی آلیسان"

urlpatterns = [
    path("health/", include("apps.common.urls")),
    path("admin/overview/", admin.site.admin_view(sales_dashboard), name="sales-dashboard"),
    path("admin/school-lists/<int:pk>/file/", admin.site.admin_view(admin_school_file), name="school-list-admin-file"),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/reviews/", include("apps.reviews.urls")),
    path("api/v1/support/", include("apps.support.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
