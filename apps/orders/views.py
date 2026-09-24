from django.db import transaction
from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from apps.inventory.models import DigitalItem

from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartItemSerializer, CartItemUpdateSerializer, CheckoutSerializer, OrderSerializer
from .services import checkout, get_or_create_cart


class CartView(generics.GenericAPIView):
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.none()

    @extend_schema(responses=CartItemSerializer(many=True))
    def get(self, request):
        cart = get_or_create_cart(request.user)
        items = cart.items.select_related("variant", "variant__product")
        return Response(CartItemSerializer(items, many=True).data)

    @transaction.atomic
    def post(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_or_create_cart(request.user, lock=True)
        variant = serializer.validated_data["variant"]
        item, _ = CartItem.objects.update_or_create(
            cart=cart, variant=variant, defaults={"quantity": serializer.validated_data["quantity"]})
        item = CartItem.objects.select_related("variant", "variant__product").get(pk=item.pk)
        return Response(CartItemSerializer(item).data, status=status.HTTP_200_OK)


class CartItemView(generics.GenericAPIView):
    serializer_class = CartItemSerializer

    @transaction.atomic
    def patch(self, request, pk):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = CartItem.objects.select_for_update().select_related(
            "variant", "variant__product").filter(pk=pk, cart__user=request.user).first()
        if not item:
            return Response(status=status.HTTP_404_NOT_FOUND)
        item.quantity = serializer.validated_data["quantity"]
        item.full_clean()
        item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item).data)

    @transaction.atomic
    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            Cart.objects.select_for_update().get(pk=cart.pk)
        CartItem.objects.filter(pk=pk, cart__user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutView(generics.GenericAPIView):
    serializer_class = CheckoutSerializer

    @extend_schema(
        parameters=[OpenApiParameter(name="Idempotency-Key", location=OpenApiParameter.HEADER,
                                     required=True, type=str,
                                     description="Stable 8-80 character key for checkout retries")],
        responses={200: OrderSerializer, 201: OrderSerializer},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order, created = checkout(request.user,
                                  idempotency_key=request.headers.get("Idempotency-Key", ""),
                                  **serializer.validated_data)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(OrderSerializer(order, context={"request": request}).data, status=response_status)


class OrderQuerysetMixin:
    serializer_class = OrderSerializer
    queryset = Order.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        items = OrderItem.objects.select_related("variant")
        if self.kwargs.get("pk"):
            codes = DigitalItem.objects.only("id", "sold_order_item_id", "encrypted_payload")
            items = items.prefetch_related(Prefetch("digital_items", queryset=codes,
                                                    to_attr="digital_codes_cache"))
        return Order.objects.filter(user=self.request.user).prefetch_related(
            Prefetch("items", queryset=items)).order_by("-created_at")


class OrderListView(OrderQuerysetMixin, generics.ListAPIView):
    pass


class OrderDetailView(OrderQuerysetMixin, generics.RetrieveAPIView):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["include_codes"] = True
        return context

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response
