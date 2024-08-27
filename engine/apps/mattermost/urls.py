from django.urls import include, path

from common.api_helpers.optional_slash_router import OptionalSlashRouter

from .views import MattermostChannelViewSet

app_name = "mattermost"
router = OptionalSlashRouter()
router.register(r"channels", MattermostChannelViewSet, basename="channel")

urlpatterns = [
    path("", include(router.urls)),
]
