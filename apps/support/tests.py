from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Ticket


class TicketAPITests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user("09123456789", is_verified=True)
        self.other = User.objects.create_user("09123456788", is_verified=True)
        self.staff = User.objects.create_user("09123456787", is_verified=True, is_staff=True, is_support=True)

    def test_customer_isolation_and_staff_lifecycle(self):
        self.client.force_authenticate(self.customer)
        created = self.client.post("/api/v1/support/tickets/", {"subject": "مشکل سفارش"})
        self.assertEqual(created.status_code, 201)
        ticket_id = created.data["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/support/tickets/{ticket_id}/").status_code, 404)
        self.client.force_authenticate(self.staff)
        status_response = self.client.patch(f"/api/v1/support/staff/tickets/{ticket_id}/status/",
                                            {"status": Ticket.Status.CLOSED})
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.data["status"], Ticket.Status.CLOSED)
