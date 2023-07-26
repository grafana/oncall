from pathlib import Path

from django.conf import settings
from django.urls import path

from apps.email.inbound import InboundEmailWebhookView
from common.api_helpers.optional_slash_router import optional_slash_path

from .views import (
    AlertManagerAPIView,
    AlertManagerV2View,
    AmazonSNS,
    GrafanaAlertingAPIView,
    GrafanaAPIView,
    IntegrationHeartBeatAPIView,
    MetadataView,
    UniversalAPIView,
)

app_name = "integrations"

# Check filenames in integrations/metadata/heartbeat for available integrations.
p = Path(__file__).parent.absolute()
PATH_TO_HEARTBEAT_DATA_DIR = p / "metadata/heartbeat"
INTEGRATIONS_WITH_HEARTBEAT_AVAILABLE = {
    f.stem
    for f in Path.iterdir(PATH_TO_HEARTBEAT_DATA_DIR)
    if Path.is_file(PATH_TO_HEARTBEAT_DATA_DIR / f) and not f.name.startswith("_")
}
# Don't forget to update model-url map in apps/alerts/models.py, AlertReceiveChannel, INTEGRATIONS_TO_REVERSE_URL_MAP
urlpatterns = [
    path("grafana/<str:alert_channel_key>/", GrafanaAPIView.as_view(), name="grafana"),
    path("grafana_alerting/<str:alert_channel_key>/", GrafanaAlertingAPIView.as_view(), name="grafana_alerting"),
    path("alertmanager/<str:alert_channel_key>/", AlertManagerAPIView.as_view(), name="alertmanager"),
    path("amazon_sns/<str:alert_channel_key>/", AmazonSNS.as_view(), name="amazon_sns"),
    path("alertmanager_v2/<str:alert_channel_key>/", AlertManagerV2View.as_view(), name="alertmanager_v2"),
    path("<str:integration_type>/<str:alert_channel_key>/", UniversalAPIView.as_view(), name="universal"),
    path("<str:integration_type>/meta/<str:alert_channel_key>/", MetadataView.as_view(), name="metadata"),
]

if settings.FEATURE_INBOUND_EMAIL_ENABLED:
    urlpatterns += [
        optional_slash_path("inbound_email_webhook", InboundEmailWebhookView.as_view(), name="inbound_email_webhook"),
    ]


def create_heartbeat_path(integration_url):
    return path(
        f"{integration_url}/<str:alert_channel_key>/heartbeat/",
        IntegrationHeartBeatAPIView.as_view(),
        name=f"{integration_url}_heartbeat",
    )


urlpatterns += [create_heartbeat_path(integration_url) for integration_url in INTEGRATIONS_WITH_HEARTBEAT_AVAILABLE]
