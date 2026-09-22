from django import forms
from django.contrib import admin

from .models import DigitalItem


class DigitalItemForm(forms.ModelForm):
    secret = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False,
                             label="کد جدید (نمایش داده نمی‌شود)")

    class Meta:
        model = DigitalItem
        fields = ("variant", "secret")

    def clean(self):
        data = super().clean()
        secret = data.get("secret")
        if not self.instance.pk and not secret:
            self.add_error("secret", "کد الزامی است.")
        if self.instance.pk and self.instance.status != DigitalItem.Status.AVAILABLE and secret:
            self.add_error("secret", "کد رزروشده یا فروخته‌شده قابل تغییر نیست.")
        if secret and "secret" not in self.errors:
            self.instance.set_secret(secret)
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


@admin.register(DigitalItem)
class DigitalItemAdmin(admin.ModelAdmin):
    form = DigitalItemForm
    list_display = ("id", "variant", "status", "masked_secret", "created_at")
    list_filter = ("status", "variant__region")
    search_fields = ("variant__sku", "id")
    readonly_fields = ("status", "reserved_order", "sold_order_item", "masked_secret")
    list_select_related = ("variant",)

    @admin.display(description="کد")
    def masked_secret(self, obj):
        return "••••••••" if obj.pk else "—"

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return (*fields, "variant") if obj else fields

    def get_queryset(self, request):
        return super().get_queryset(request).defer("encrypted_payload")
