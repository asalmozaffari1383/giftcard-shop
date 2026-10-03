from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from apps.common.admin import AdminRoleRequiredMixin

from .catalog import ensure_sources, parse_uploaded_catalog, publish_candidate, upsert_candidates
from .forms import CatalogUploadForm
from .models import CatalogCandidate, CatalogImportBatch, CatalogSource, FeedSyncLog


@admin.register(CatalogSource)
class CatalogSourceAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("name", "kind", "is_active", "candidate_count", "last_synced_at")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "slug", "base_url")
    readonly_fields = ("last_synced_at", "created_at", "updated_at")
    actions = ("queue_sync",)

    @admin.display(description="تعداد محصولات")
    def candidate_count(self, obj):
        return obj.candidates.count()

    @admin.action(description="همگام‌سازی منابع انتخاب‌شده")
    def queue_sync(self, request, queryset):
        from .tasks import sync_catalog_source

        count = 0
        for source in queryset.filter(is_active=True):
            transaction.on_commit(lambda source_id=source.pk: sync_catalog_source.delay(source_id))
            count += 1
        self.message_user(request, f"همگام‌سازی {count} منبع در صف قرار گرفت.", messages.SUCCESS)


@admin.register(CatalogCandidate)
class CatalogCandidateAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    change_list_template = "admin/integrations/catalogcandidate/change_list.html"
    list_display = ("title", "source", "duplicate_count", "price_display", "availability", "review_status",
                    "matched_product_link", "last_seen_at")
    list_filter = ("source", "review_status", "availability", "source_currency")
    search_fields = ("title", "normalized_title", "source_sku", "external_id", "source_url")
    readonly_fields = ("normalized_title", "last_seen_at", "created_at", "updated_at", "raw_data",
                       "matched_product")
    autocomplete_fields = ("source",)
    list_select_related = ("source", "matched_product")
    list_per_page = 50
    actions = ("approve", "reject", "publish")

    def get_queryset(self, request):
        duplicates = CatalogCandidate.objects.filter(
            normalized_title=OuterRef("normalized_title"),
        ).values("normalized_title").annotate(total=Count("id")).values("total")
        return super().get_queryset(request).annotate(
            _duplicate_count=Subquery(duplicates, output_field=IntegerField()))

    def get_urls(self):
        custom = [path("import/", self.admin_site.admin_view(self.import_view),
                       name="integrations_catalogcandidate_import")]
        return custom + super().get_urls()

    def import_view(self, request):
        ensure_sources()
        form = CatalogUploadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            source = form.cleaned_data["source"]
            uploaded = form.cleaned_data["catalog_file"]
            try:
                candidates = parse_uploaded_catalog(uploaded, uploaded.name)
                discovered, created, updated = upsert_candidates(source, candidates)
            except (ValueError, TypeError) as exc:
                form.add_error("catalog_file", str(exc))
            else:
                self.message_user(
                    request,
                    f"{discovered} ردیف پردازش شد؛ {created} محصول جدید و {updated} محصول به‌روزشده.",
                    messages.SUCCESS,
                )
                return redirect(reverse("admin:integrations_catalogcandidate_changelist"))
        context = {
            **self.admin_site.each_context(request),
            "title": "ورود گروهی محصولات",
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/integrations/catalogcandidate/import_form.html", context)

    @admin.display(description="قیمت منبع", ordering="source_price")
    def price_display(self, obj):
        if obj.source_price is None:
            return "—"
        currency = obj.source_currency or "واحد منبع"
        return f"{obj.source_price:,} {currency}"

    @admin.display(description="منابع مشابه", ordering="_duplicate_count")
    def duplicate_count(self, obj):
        return obj._duplicate_count

    @admin.display(description="محصول کاتالوگ")
    def matched_product_link(self, obj):
        if not obj.matched_product_id:
            return "—"
        url = reverse("admin:catalog_product_change", args=(obj.matched_product_id,))
        return format_html('<a href="{}">{}</a>', url, obj.matched_product)

    @admin.action(description="تأیید موارد انتخاب‌شده")
    def approve(self, request, queryset):
        count = queryset.filter(review_status=CatalogCandidate.ReviewStatus.PENDING).update(
            review_status=CatalogCandidate.ReviewStatus.APPROVED)
        self.message_user(request, f"{count} مورد تأیید شد.", messages.SUCCESS)

    @admin.action(description="رد موارد انتخاب‌شده")
    def reject(self, request, queryset):
        count = queryset.exclude(review_status=CatalogCandidate.ReviewStatus.IMPORTED).update(
            review_status=CatalogCandidate.ReviewStatus.REJECTED)
        self.message_user(request, f"{count} مورد رد شد.", messages.WARNING)

    @admin.action(description="ساخت محصول غیرفعال از موارد انتخاب‌شده")
    def publish(self, request, queryset):
        imported = 0
        skipped = 0
        for candidate in queryset.select_related("source"):
            if candidate.review_status not in {
                    CatalogCandidate.ReviewStatus.APPROVED,
                    CatalogCandidate.ReviewStatus.IMPORTED,
            }:
                skipped += 1
                continue
            publish_candidate(candidate)
            imported += 1
        self.message_user(
            request,
            f"{imported} محصول غیرفعال ساخته/متصل شد؛ {skipped} مورد به‌دلیل تأییدنشدن رد شد.",
            messages.SUCCESS if imported else messages.WARNING,
        )


@admin.register(CatalogImportBatch)
class CatalogImportBatchAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("id", "source", "status", "discovered_count", "created_count", "updated_count",
                    "error_count", "created_at", "finished_at")
    list_filter = ("status", "source", "created_at")
    readonly_fields = ("source", "status", "discovered_count", "created_count", "updated_count",
                       "error_count", "error_message", "finished_at", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FeedSyncLog)
class FeedSyncLogAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("partner", "page", "product_count", "created_at")
    list_filter = ("partner", "created_at")
    readonly_fields = ("partner", "page", "product_count", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
