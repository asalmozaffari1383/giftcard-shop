from django.urls import path

from .views import InitiatePaymentView, PaymentCallbackView, RecordRefundView

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view()),
    path("callback/<uuid:payment_id>/", PaymentCallbackView.as_view()),
    path("<uuid:payment_id>/refund-record/", RecordRefundView.as_view()),
]
