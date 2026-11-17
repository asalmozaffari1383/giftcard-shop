from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.parsers import MultiPartParser, FormParser

from apps.common.admin import AdminRoleRequiredMixin
from .models import SchoolList


class SchoolListSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = SchoolList
        fields = ("id", "title", "notes", "file", "status", "quoted_total", "admin_reply", "created_at")
        read_only_fields = ("id", "status", "quoted_total", "admin_reply", "created_at")

    def validate_file(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("حداکثر حجم فایل ۵ مگابایت است.")
        content = value.read()
        if content.startswith(b"%PDF-"):
            return (content, "application/pdf")
        try:
            with Image.open(BytesIO(content)) as image:
                if image.format not in ("JPEG", "PNG") or image.width * image.height > 20000000:
                    raise serializers.ValidationError("تصویر باید JPG یا PNG با حداکثر ۲۰ مگاپیکسل باشد.")
                file_type = "image/png" if image.format == "PNG" else "image/jpeg"
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise serializers.ValidationError("فقط تصویر معتبر JPG/PNG یا PDF بفرستید.") from exc
        return (content, file_type)

    def create(self, validated_data):
        content, file_type = validated_data.pop("file")
        return SchoolList.objects.create(file_content=content, file_type=file_type, **validated_data)


class SchoolListView(generics.ListCreateAPIView):
    serializer_class = SchoolListSerializer
    queryset = SchoolList.objects.none()
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return self.queryset
        return SchoolList.objects.filter(user=self.request.user).defer("file_content")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def file_response(item):
    extension = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}[item.file_type]
    response = HttpResponse(bytes(item.file_content), content_type=item.file_type)
    response["Content-Disposition"] = f'attachment; filename="school-list-{item.pk}.{extension}"'
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


class SchoolListFileView(generics.GenericAPIView):
    serializer_class = SchoolListSerializer

    def get(self, request, pk):
        return file_response(get_object_or_404(SchoolList, pk=pk, user=request.user))


def admin_school_file(request, pk):
    if not AdminRoleRequiredMixin._has_admin_role(request):
        raise PermissionDenied
    return file_response(get_object_or_404(SchoolList, pk=pk))
