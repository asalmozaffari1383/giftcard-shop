from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.common.admin import AdminRoleRequiredMixin

from .models import OTPChallenge, Profile, User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("phone_number",)

    def clean_password2(self):
        if self.cleaned_data.get("password1") != self.cleaned_data.get("password2"):
            raise forms.ValidationError("رمزها مطابقت ندارند.")
        return self.cleaned_data["password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(AdminRoleRequiredMixin, BaseUserAdmin):
    add_form = UserCreationForm
    list_display = ("phone_number", "is_verified", "is_staff", "is_support", "date_joined")
    list_filter = ("is_verified", "is_staff", "is_support", "is_active")
    search_fields = ("phone_number",)
    ordering = ("-date_joined",)
    fieldsets = ((None, {"fields": ("phone_number", "password")}),
                 ("دسترسی", {"fields": ("is_active", "is_verified", "is_staff", "is_support",
                                           "is_admin", "is_superuser", "groups", "user_permissions")}))
    add_fieldsets = ((None, {"fields": ("phone_number", "password1", "password2")}),)


@admin.register(Profile)
class ProfileAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    search_fields = ("user__phone_number", "first_name", "last_name")


@admin.register(OTPChallenge)
class OTPAdmin(AdminRoleRequiredMixin, admin.ModelAdmin):
    list_display = ("phone_number", "created_at", "expires_at", "attempts", "consumed_at")
    readonly_fields = ("phone_number", "code_hash", "created_at", "expires_at", "attempts", "consumed_at")
    search_fields = ("phone_number",)

    def has_add_permission(self, request):
        return False
