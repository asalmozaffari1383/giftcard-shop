from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.common.permissions import IsStaffRole

from .models import Ticket, TicketMessage
from .serializers import InquirySerializer, MessageSerializer, TicketSerializer, TicketStatusSerializer


class TicketListView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return Ticket.objects.filter(user=self.request.user).prefetch_related("messages").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = TicketSerializer

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user).prefetch_related("messages")


class TicketReplyView(generics.GenericAPIView):
    serializer_class = MessageSerializer

    @extend_schema(responses={201: MessageSerializer})
    def post(self, request, pk):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().filter(pk=pk, user=request.user).first()
            if not ticket or ticket.status == Ticket.Status.CLOSED:
                raise ValidationError("تیکت باز یافت نشد.")
            message = TicketMessage.objects.create(ticket=ticket, author=request.user,
                                                    body=serializer.validated_data["body"])
            ticket.status = Ticket.Status.WAITING
            ticket.save(update_fields=["status", "updated_at"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class StaffTicketListView(generics.ListAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsStaffRole]
    queryset = Ticket.objects.select_related("user").prefetch_related("messages").order_by("-updated_at")
    filterset_fields = ("status",)
    search_fields = ("subject", "user__phone_number")


class StaffTicketReplyView(generics.GenericAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsStaffRole]

    @extend_schema(responses={201: MessageSerializer})
    def post(self, request, pk):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().filter(pk=pk).first()
            if not ticket or ticket.status == Ticket.Status.CLOSED:
                raise ValidationError("تیکت باز یافت نشد.")
            message = TicketMessage.objects.create(ticket=ticket, author=request.user,
                                                    body=serializer.validated_data["body"])
            ticket.status = Ticket.Status.OPEN
            ticket.save(update_fields=["status", "updated_at"])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class StaffTicketStatusView(generics.GenericAPIView):
    serializer_class = TicketStatusSerializer
    permission_classes = [IsStaffRole]

    def patch(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().filter(pk=pk).first()
            if not ticket:
                raise ValidationError("تیکت یافت نشد.")
            ticket.status = serializer.validated_data["status"]
            ticket.save(update_fields=["status", "updated_at"])
        return Response(TicketSerializer(ticket, context={"request": request}).data)


class TicketCloseView(generics.GenericAPIView):
    serializer_class = TicketStatusSerializer

    @extend_schema(request=None, responses=TicketSerializer)
    def post(self, request, pk):
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().filter(pk=pk, user=request.user).first()
            if not ticket:
                raise ValidationError("تیکت یافت نشد.")
            ticket.status = Ticket.Status.CLOSED
            ticket.save(update_fields=["status", "updated_at"])
        return Response(TicketSerializer(ticket, context={"request": request}).data)


class InquiryView(generics.CreateAPIView):
    serializer_class = InquirySerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "inquiry"
