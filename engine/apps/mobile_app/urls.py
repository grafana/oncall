from django.conf import settings

from apps.mobile_app.fcm_relay import FCMRelayView
from apps.mobile_app.views import APNSDeviceAuthorizedViewSet, FCMDeviceAuthorizedViewSet, MobileAppAuthTokenAPIView
from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

app_name = "mobile_app"
router = OptionalSlashRouter()

router.register("apns", APNSDeviceAuthorizedViewSet, basename="apns")
router.register("fcm", FCMDeviceAuthorizedViewSet, basename="fcm")

urlpatterns = [
    *router.urls,
    optional_slash_path("auth_token", MobileAppAuthTokenAPIView.as_view(), name="auth_token"),
]

if settings.FCM_RELAY_ENABLED:
    urlpatterns += [
        optional_slash_path("fcm_relay", FCMRelayView.as_view(), name="fcm_relay"),
    ]
