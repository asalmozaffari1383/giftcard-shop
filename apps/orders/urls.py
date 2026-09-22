from django.urls import path

from .views import CartItemView, CartView, CheckoutView, OrderDetailView, OrderListView

urlpatterns = [
    path("cart/", CartView.as_view()), path("cart/items/<int:pk>/", CartItemView.as_view()),
    path("checkout/", CheckoutView.as_view()), path("", OrderListView.as_view()),
    path("<uuid:pk>/", OrderDetailView.as_view()),
]
