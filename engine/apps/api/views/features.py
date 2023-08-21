from django.conf import settings
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings

FEATURE_SLACK = "slack"
FEATURE_TELEGRAM = "telegram"
FEATURE_LIVE_SETTINGS = "live_settings"
FEATURE_GRAFANA_CLOUD_NOTIFICATIONS = "grafana_cloud_notifications"
FEATURE_GRAFANA_CLOUD_CONNECTION = "grafana_cloud_connection"
FEATURE_GRAFANA_ALERTING_V2 = "grafana_alerting_v2"


class FeaturesAPIView(APIView):
    """
    Return whitelist of enabled features.
    It is needed to disable features for On-prem installations.
    """

    authentication_classes = (PluginAuthentication,)

    @extend_schema(
        request=None,
        responses=serializers.ListField(child=serializers.CharField()),
        examples=[
            OpenApiExample(
                name="Example response",
                value=["slack", "telegram", "grafana_cloud_connection", "live_settings", "grafana_cloud_notifications"],
            )
        ],
    )
    def get(self, request):
        data = self._get_enabled_features(request)
        return Response(data)

    def _get_enabled_features(self, request):
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

        if settings.FEATURE_GRAFANA_ALERTING_V2_ENABLED:
            enabled_features.append(FEATURE_GRAFANA_ALERTING_V2)

        return enabled_features
