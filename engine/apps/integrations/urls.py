from pathlib import Path

from django.urls import path

from .views import (
    AlertManagerAPIView,
    AmazonSNS,
    GrafanaAlertingAPIView,
    GrafanaAPIView,
    HeartBeatAPIView,
    IntegrationHeartBeatAPIView,
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
    path("heartbeat/<str:alert_channel_key>/", HeartBeatAPIView.as_view(), name="heartbeat"),
    path("<str:integration_type>/<str:alert_channel_key>/", UniversalAPIView.as_view(), name="universal"),
]


def create_heartbeat_path(integration_url):
    return path(
        f"{integration_url}/<str:alert_channel_key>/heartbeat/",
        IntegrationHeartBeatAPIView.as_view(),
        name=f"{integration_url}_heartbeat",
    )


urlpatterns += [create_heartbeat_path(integration_url) for integration_url in INTEGRATIONS_WITH_HEARTBEAT_AVAILABLE]
