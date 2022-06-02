from django.apps import apps
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication

FEATURE_SLACK = "slack"
FEATURE_TELEGRAM = "telegram"
FEATURE_LIVE_SETTINGS = "live_settings"
MOBILE_APP_PUSH_NOTIFICATIONS = "mobile_app"


class FeaturesAPIView(APIView):
    """
    Return whitelist of enabled features.
    It is needed to disable features for On-prem installations.
    """

    authentication_classes = (PluginAuthentication,)

    def get(self, request):
        return Response(self._get_enabled_features(request))

    def _get_enabled_features(self, request):
        enabled_features = []

        if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
            enabled_features.append(FEATURE_SLACK)

        if settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
            enabled_features.append(FEATURE_TELEGRAM)

        if settings.FEATURE_LIVE_SETTINGS_ENABLED:
            enabled_features.append(FEATURE_LIVE_SETTINGS)

        if settings.MOBILE_APP_PUSH_NOTIFICATIONS_ENABLED:
            DynamicSetting = apps.get_model("base", "DynamicSetting")
            mobile_app_settings = DynamicSetting.objects.get_or_create(
                name="mobile_app_settings",
                defaults={
                    "json_value": {
                        "org_ids": [],
                    }
                },
            )[0]

            if request.auth.organization.pk in mobile_app_settings.json_value["org_ids"]:
                enabled_features.append(MOBILE_APP_PUSH_NOTIFICATIONS)

        return enabled_features
