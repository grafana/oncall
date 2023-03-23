from apps.mobile_app.fcm_relay import FCMRelayView
from apps.mobile_app.views import FCMDeviceAuthorizedViewSet, MobileAppAuthTokenAPIView, MobileAppUserSettingsAPIView
from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

app_name = "mobile_app"
router = OptionalSlashRouter()

router.register("fcm", FCMDeviceAuthorizedViewSet, basename="fcm")

urlpatterns = [
    *router.urls,
    optional_slash_path("auth_token", MobileAppAuthTokenAPIView.as_view(), name="auth_token"),
    optional_slash_path("user_settings", MobileAppUserSettingsAPIView.as_view(), name="user_settings"),
]

urlpatterns += [
    optional_slash_path("fcm_relay", FCMRelayView.as_view(), name="fcm_relay"),
]
