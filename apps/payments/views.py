from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.permissions import IsAdminRole

from .serializers import PaymentRequestSerializer, PaymentSerializer, RefundRecordSerializer, RefundSerializer
from .services import initiate_payment, record_external_refund, verify_callback


class InitiatePaymentView(generics.GenericAPIView):
    serializer_class = PaymentRequestSerializer

    @extend_schema(responses={201: PaymentSerializer})
    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment, url = initiate_payment(request.user, **serializer.validated_data)
        return Response({"payment": PaymentSerializer(payment).data, "payment_url": url},
                        status=status.HTTP_201_CREATED)


class PaymentCallbackView(generics.GenericAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    @extend_schema(parameters=[], responses=PaymentSerializer)
    def get(self, request, payment_id):
        authority = request.query_params.get("Authority", "")
        gateway_status = request.query_params.get("Status", "")
        payment = verify_callback(payment_id, authority, gateway_status)
        return Response(PaymentSerializer(payment).data)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class RecordRefundView(generics.GenericAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = RefundRecordSerializer

    @extend_schema(responses={201: RefundSerializer})
    def post(self, request, payment_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = record_external_refund(payment_id, serializer.validated_data["external_reference"], request.user)
        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)
