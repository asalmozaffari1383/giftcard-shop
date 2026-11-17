from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from .views import (AddressDetailView, AddressListCreateView, BenefitsView, MeView, ProfileView, RequestOTPView,
                    VerifyOTPView, WishlistItemDetailView, WishlistView)

urlpatterns = [
    path("otp/request/", RequestOTPView.as_view()), path("otp/verify/", VerifyOTPView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()), path("token/logout/", TokenBlacklistView.as_view()),
    path("me/", MeView.as_view()), path("profile/", ProfileView.as_view()),
    path("benefits/", BenefitsView.as_view()),
    path("addresses/", AddressListCreateView.as_view()), path("addresses/<int:pk>/", AddressDetailView.as_view()),
    path("wishlist/", WishlistView.as_view()), path("wishlist/<int:pk>/", WishlistItemDetailView.as_view()),
]
