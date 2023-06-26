from django.urls import path
from .views import CallStatusCallback, HealthCheck

app_name = "zvonok"

urlpatterns = [
    path("call_status_events", CallStatusCallback.as_view(), name="call_status_events"),
    path("healthz", HealthCheck.as_view()),
]
