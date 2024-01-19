from django.urls import path

from .views import WebHookView

app_name = "telegram"

urlpatterns = [
    path("", WebHookView.as_view(), name="incoming_webhook"),
    path("v3/", WebHookView.as_view(), name="incoming_webhook"),
]
