from django.urls import path

from apps.sendgridapp.views import EmailStatusCallback

app_name = "sendgridapp"

urlpatterns = [
    path(r"email_status_event/", EmailStatusCallback.as_view(), name="email_status_event"),
]
