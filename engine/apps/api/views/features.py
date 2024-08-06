import enum

from django.conf import settings
from drf_spectacular.plumbing import resolve_type_hint
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings
from apps.labels.utils import is_labels_feature_enabled


class Feature(enum.StrEnum):
    MSTEAMS = "msteams"
    SLACK = "slack"
    UNIFIED_SLACK = "unified_slack"
    TELEGRAM = "telegram"
    LIVE_SETTINGS = "live_settings"
    GRAFANA_CLOUD_NOTIFICATIONS = "grafana_cloud_notifications"
    GRAFANA_CLOUD_CONNECTION = "grafana_cloud_connection"
    # GRAFANA_ALERTING_V2 enables advanced OnCall <-> Alerting integration.
    # On Alerting side it enables integration dropdown in OnCall contact point.
    # On OnCall side it do nothing, just indicating if OnCall API is ready to that integration.
    GRAFANA_ALERTING_V2 = "grafana_alerting_v2"
    LABELS = "labels"
    GOOGLE_OAUTH2 = "google_oauth2"
    SERVICE_DEPENDENCIES = "service_dependencies"
<<<<<<< HEAD
    PERSONAL_WEBHOOK = "personal_webhook"
=======
    MATTERMOST = "mattermost"
>>>>>>> 99ba40e8b (Add mattermost OAuth2 flow)


class FeaturesAPIView(APIView):
    """
    Return whitelist of enabled features.
    It is needed to disable features for On-prem installations.
    """

    authentication_classes = (PluginAuthentication,)

    @extend_schema(responses={status.HTTP_200_OK: resolve_type_hint(list[Feature])})
    def get(self, request):
        data = self._get_enabled_features(request)
        return Response(data)

    def _get_enabled_features(self, request):
        enabled_features = []

        if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
            enabled_features.append(Feature.SLACK)

        if settings.UNIFIED_SLACK_APP_ENABLED:
            enabled_features.append(Feature.UNIFIED_SLACK)

        if settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
            enabled_features.append(Feature.TELEGRAM)

        if settings.IS_OPEN_SOURCE:
            # Features below should be enabled only in OSS
            enabled_features.append(Feature.GRAFANA_CLOUD_CONNECTION)
            if settings.FEATURE_LIVE_SETTINGS_ENABLED:
                enabled_features.append(Feature.LIVE_SETTINGS)
            if live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED:
                enabled_features.append(Feature.GRAFANA_CLOUD_NOTIFICATIONS)
        else:
            enabled_features.append(Feature.MSTEAMS)

        if settings.FEATURE_GRAFANA_ALERTING_V2_ENABLED:
            enabled_features.append(Feature.GRAFANA_ALERTING_V2)

        if is_labels_feature_enabled(self.request.auth.organization):
            enabled_features.append(Feature.LABELS)

        if settings.GOOGLE_OAUTH2_ENABLED:
            enabled_features.append(Feature.GOOGLE_OAUTH2)

        if settings.FEATURE_SERVICE_DEPENDENCIES_ENABLED:
            enabled_features.append(Feature.SERVICE_DEPENDENCIES)

        if settings.FEATURE_PERSONAL_WEBHOOK_ENABLED:
            enabled_features.append(Feature.PERSONAL_WEBHOOK)

        if settings.FEATURE_MATTERMOST_INTEGRATION_ENABLED:
            enabled_features.append(Feature.MATTERMOST)

        return enabled_features
