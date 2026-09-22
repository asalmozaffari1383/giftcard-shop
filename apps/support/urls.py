from django.urls import path

from .views import (InquiryView, StaffTicketListView, StaffTicketReplyView,
                    TicketDetailView, TicketListView, TicketReplyView)

urlpatterns = [
    path("tickets/", TicketListView.as_view()), path("tickets/<int:pk>/", TicketDetailView.as_view()),
    path("tickets/<int:pk>/messages/", TicketReplyView.as_view()),
    path("staff/tickets/", StaffTicketListView.as_view()),
    path("staff/tickets/<int:pk>/messages/", StaffTicketReplyView.as_view()),
    path("inquiries/", InquiryView.as_view()),
]
