from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F
from django.utils import timezone
from apps.orders.models import Coupon

from .models import Address, Profile, WishlistItem
from .serializers import (AddressSerializer, PhoneSerializer, ProfileSerializer, UserSerializer,
                          VerifyOTPSerializer, WishlistItemSerializer)
from .services import request_otp, verify_otp


class RequestOTPView(generics.GenericAPIView):
    serializer_class = PhoneSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(responses={202: None})
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_otp(serializer.validated_data["phone_number"])
        return Response({"detail": "در صورت معتبر بودن شماره، کد ارسال شد."}, status=status.HTTP_202_ACCEPTED)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp"

    @extend_schema(responses=UserSerializer)
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = verify_otp(**serializer.validated_data)
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh),
                         "user": UserSerializer(user).data})


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class BenefitsView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request):
        now = timezone.now()
        coupons = Coupon.objects.filter(assigned_user=request.user, is_active=True, starts_at__lte=now,
                                        ends_at__gt=now, used_count__lt=F("usage_limit"))
        birthday = getattr(getattr(request.user, "profile", None), "birth_date", None)
        today = timezone.localdate()
        if not birthday or (birthday.month, birthday.day) != (today.month, today.day):
            coupons = coupons.filter(birthday_only=False)
        return Response({"coupons": list(coupons.values("code", "percent_off", "amount_off", "ends_at"))})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    pagination_class = None
    queryset = Address.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return self.queryset
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistItemSerializer
    pagination_class = None
    queryset = WishlistItem.objects.none()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=serializer.validated_data["product"])
        return Response(self.get_serializer(item).data, status=201 if created else 200)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return self.queryset
        return WishlistItem.objects.filter(user=self.request.user).select_related("product")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistItemDetailView(generics.DestroyAPIView):
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)
