from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from .views import MeView, ProfileView, RequestOTPView, VerifyOTPView

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view()), path("otp/verify/", VerifyOTPView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()), path("token/logout/", TokenBlacklistView.as_view()),
    path("me/", MeView.as_view()), path("profile/", ProfileView.as_view()),
]
