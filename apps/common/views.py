import uuid

from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class LivenessView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response({"status": "ok"})


class ReadinessView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(responses={200: dict, 503: dict})
    def get(self, request):
        components = {"database": False, "cache": False}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                components["database"] = cursor.fetchone() == (1,)
        except Exception:
            components["database"] = False
        cache_key = f"health:{uuid.uuid4()}"
        try:
            cache.set(cache_key, "ok", timeout=10)
            components["cache"] = cache.get(cache_key) == "ok"
            cache.delete(cache_key)
        except Exception:
            components["cache"] = False
        ready = all(components.values())
        response_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({"status": "ok" if ready else "unavailable", "components": components},
                        status=response_status)
