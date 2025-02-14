from django.urls import include, path

from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

from .views import MattermostChannelViewSet, MattermostEventView

app_name = "mattermost"
router = OptionalSlashRouter()
router.register(r"channels", MattermostChannelViewSet, basename="channel")

urlpatterns = [
    path("", include(router.urls)),
    optional_slash_path("event", MattermostEventView.as_view(), name="incoming_mattermost_event"),
]
