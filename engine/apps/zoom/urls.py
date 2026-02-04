from django.urls import include, path

from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

from .views import ZoomChannelViewSet, ZoomEventView, ZoomWebhookView

router = OptionalSlashRouter()
router.register(r"channels", ZoomChannelViewSet, basename="channel")

urlpatterns = [
    path("", include(router.urls)),
    optional_slash_path("event", ZoomEventView.as_view(), name="incoming_zoom_event"),
    optional_slash_path("webhook", ZoomWebhookView.as_view(), name="zoom_webhook"),
]
