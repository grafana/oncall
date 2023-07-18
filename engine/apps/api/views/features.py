from django.apps import apps
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings

FEATURE_SLACK = "slack"
FEATURE_TELEGRAM = "telegram"
FEATURE_LIVE_SETTINGS = "live_settings"
FEATURE_GRAFANA_CLOUD_NOTIFICATIONS = "grafana_cloud_notifications"
FEATURE_GRAFANA_CLOUD_CONNECTION = "grafana_cloud_connection"
FEATURE_WEB_SCHEDULES = "web_schedules"
FEATURE_WEBHOOKS2 = "webhooks2"


class FeaturesAPIView(APIView):
    """
    Return whitelist of enabled features.
    It is needed to disable features for On-prem installations.
    """

    authentication_classes = (PluginAuthentication,)

    def get(self, request):
        return Response(self._get_enabled_features(request))

    def _get_enabled_features(self, request):
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        enabled_features = []

        if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
            enabled_features.append(FEATURE_SLACK)

        if settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
            enabled_features.append(FEATURE_TELEGRAM)

        if settings.IS_OPEN_SOURCE:
            # Features below should be enabled only in OSS
            enabled_features.append(FEATURE_GRAFANA_CLOUD_CONNECTION)
            if settings.FEATURE_LIVE_SETTINGS_ENABLED:
                enabled_features.append(FEATURE_LIVE_SETTINGS)
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                enabled_features.append(FEATURE_GRAFANA_CLOUD_NOTIFICATIONS)

        if settings.FEATURE_WEB_SCHEDULES_ENABLED:
            enabled_features.append(FEATURE_WEB_SCHEDULES)
        else:
            # allow enabling web schedules per org, independently of global status flag
            enabled_web_schedules_orgs = DynamicSetting.objects.get_or_create(
                name="enabled_web_schedules_orgs",
                defaults={
                    "json_value": {
                        "org_ids": [],
                    }
                },
            )[0]
            if request.auth.organization.pk in enabled_web_schedules_orgs.json_value["org_ids"]:
                enabled_features.append(FEATURE_WEB_SCHEDULES)

        if settings.FEATURE_WEBHOOKS_2_ENABLED:
            enabled_features.append(FEATURE_WEBHOOKS2)

        return enabled_features
