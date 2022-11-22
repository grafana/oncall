from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet as BaseAPNSDeviceAuthorizedViewSet

from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication


class APNSDeviceAuthorizedViewSet(BaseAPNSDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
