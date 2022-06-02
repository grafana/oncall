from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet

from apps.auth_token.auth import MobileAppAuthTokenAuthentication, PluginAuthentication


class APNSDeviceAuthorizedViewSet(APNSDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication, PluginAuthentication)
