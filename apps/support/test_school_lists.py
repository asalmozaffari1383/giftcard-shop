from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.users.models import User
from .models import SchoolList


class SchoolListTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("09123456789", is_verified=True)
        self.client.force_authenticate(self.user)

    def upload(self):
        content = BytesIO()
        Image.new("RGB", (20, 20), "white").save(content, format="PNG")
        return self.client.post("/api/v1/support/school-lists/", {"title": "پایه اول", "file": SimpleUploadedFile("list.png", content.getvalue(), content_type="image/png")}, format="multipart")

    def test_upload_and_quotation_are_private(self):
        response = self.upload()
        self.assertEqual(response.status_code, 201)
        item = SchoolList.objects.get()
        item.status = "QUOTED"
        item.quoted_total = 250000
        item.admin_reply = "دفتر و مداد"
        item.full_clean()
        item.save()
        listing = self.client.get("/api/v1/support/school-lists/")
        self.assertEqual(listing.data["results"][0]["quoted_total"], 250000)
        self.assertNotIn("file_content", listing.data["results"][0])
        download = self.client.get(f"/api/v1/support/school-lists/{item.pk}/file/")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["Cache-Control"], "no-store")
        self.client.force_authenticate(User.objects.create_user("09123456788"))
        self.assertEqual(self.client.get(f"/api/v1/support/school-lists/{item.pk}/file/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/support/school-lists/").data["count"], 0)

    def test_executable_upload_disguised_as_image_is_rejected(self):
        response = self.client.post("/api/v1/support/school-lists/", {"title": "لیست", "file": SimpleUploadedFile("bad.png", b"<script>alert(1)</script>", content_type="image/png")}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(SchoolList.objects.exists())

    def test_oversize_upload_is_rejected(self):
        response = self.client.post("/api/v1/support/school-lists/", {"title": "لیست", "file": SimpleUploadedFile("huge.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024), content_type="application/pdf")}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_anonymous_upload_is_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.upload().status_code, 401)
