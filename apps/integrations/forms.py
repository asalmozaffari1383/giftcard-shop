from django import forms

from .models import CatalogSource


class CatalogUploadForm(forms.Form):
    source = forms.ModelChoiceField(queryset=CatalogSource.objects.all(), label="منبع")
    catalog_file = forms.FileField(label="فایل JSON یا CSV")

    def clean_catalog_file(self):
        uploaded = self.cleaned_data["catalog_file"]
        if uploaded.size > 5 * 1024 * 1024:
            raise forms.ValidationError("حجم فایل نباید بیشتر از ۵ مگابایت باشد.")
        if not uploaded.name.lower().endswith((".json", ".csv")):
            raise forms.ValidationError("فقط فایل JSON یا CSV قابل قبول است.")
        return uploaded
