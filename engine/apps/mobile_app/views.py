from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet as BaseAPNSDeviceAuthorizedViewSet
from push_notifications.api.rest_framework import GCMDeviceAuthorizedViewSet as BaseGCMDeviceAuthorizedViewSet

from apps.mobile_app.auth import MobileAppAuthTokenAuthentication


class APNSDeviceAuthorizedViewSet(BaseAPNSDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication,)


class GCMDeviceAuthorizedViewSet(BaseGCMDeviceAuthorizedViewSet):
    authentication_classes = (MobileAppAuthTokenAuthentication,)
