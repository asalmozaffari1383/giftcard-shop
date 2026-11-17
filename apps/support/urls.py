from django.urls import path
from .school_lists import SchoolListFileView, SchoolListView

from .views import (
    InquiryView,
    StaffTicketListView,
    StaffTicketReplyView,
    StaffTicketStatusView,
    TicketCloseView,
    TicketDetailView,
    TicketListView,
    TicketReplyView,
)

urlpatterns = [
    path("school-lists/", SchoolListView.as_view()),
    path("school-lists/<int:pk>/file/", SchoolListFileView.as_view()),
    path("tickets/", TicketListView.as_view()), path("tickets/<int:pk>/", TicketDetailView.as_view()),
    path("tickets/<int:pk>/messages/", TicketReplyView.as_view()),
    path("tickets/<int:pk>/close/", TicketCloseView.as_view()),
    path("staff/tickets/", StaffTicketListView.as_view()),
    path("staff/tickets/<int:pk>/messages/", StaffTicketReplyView.as_view()),
    path("staff/tickets/<int:pk>/status/", StaffTicketStatusView.as_view()),
    path("inquiries/", InquiryView.as_view()),
]
