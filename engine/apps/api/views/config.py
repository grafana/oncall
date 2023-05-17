from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.base.models import LiveSetting
from apps.phone_notifications.phone_provider import get_phone_provider


class ConfigApiView(APIView):
    """
    ConfigApiView return config of running OnCall instance.

    This view is needed to pass config changes to frontend
    """

    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        LiveSetting.populate_settings_if_needed()

        return {"phone_provider": self._get_phone_provider_config()}

    def _get_phone_provider_config(self):
        config = get_phone_provider().config
        return {
            "test_sms": config.test_sms,
            "test_call": config.test_call,
            "verify_sms": config.verification_sms,
            "verify_call": config.verification_call,
            "configured": config.configured,
        }
