from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet

from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication


class APNSDeviceAuthorizedViewSet(APNSDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
