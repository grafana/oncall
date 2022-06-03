from django.urls import path

from .views import CallStatusCallback, GatherView, HealthCheckView, SMSStatusCallback

app_name = "twilioapp"

urlpatterns = [
    path("healthz", HealthCheckView.as_view()),
    path("gather/", GatherView.as_view(), name="gather"),
    path("sms_status_events/", SMSStatusCallback.as_view(), name="sms_status_events"),
    path("call_status_events/", CallStatusCallback.as_view(), name="call_status_events"),
]
