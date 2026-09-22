from django.urls import path

from .views import ReviewViewSet

urlpatterns = [path("", ReviewViewSet.as_view({"get": "list", "post": "create"}), name="reviews")]
