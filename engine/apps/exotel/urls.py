from django.urls import path

from .views import CallStatusCallback

app_name = "exotel"

urlpatterns = [
    path("call_status_events/", CallStatusCallback.as_view(), name="call_status_events"),
]
