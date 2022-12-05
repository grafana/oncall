from django.urls import include, path

from apps.webhooks.views import WebhooksView
from common.api_helpers.optional_slash_router import OptionalSlashRouter

app_name = "webhooks"

router = OptionalSlashRouter()
router.register(
    r"webhooks",
    WebhooksView,
    basename="webhooks",
)

urlpatterns = [
    path("", include(router.urls)),
]
