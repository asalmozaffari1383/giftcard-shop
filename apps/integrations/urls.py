from django.urls import path

from .views import TorobFeedView

urlpatterns = [path("torob/products/", TorobFeedView.as_view())]
