from apps.mobile_app.fcm_relay import FCMRelayView
from apps.mobile_app.views import FCMDeviceAuthorizedViewSet, MobileAppAuthTokenAPIView, MobileAppUserSettingsViewSet
from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

app_name = "mobile_app"
router = OptionalSlashRouter()

router.register("fcm", FCMDeviceAuthorizedViewSet, basename="fcm")

urlpatterns = [
    *router.urls,
    optional_slash_path("auth_token", MobileAppAuthTokenAPIView.as_view(), name="auth_token"),
    optional_slash_path(
        "user_settings/notification_timing_options",
        MobileAppUserSettingsViewSet.as_view({"get": "notification_timing_options"}),
        name="notification_timing_options",
    ),
    optional_slash_path(
        "user_settings",
        MobileAppUserSettingsViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update"}),
        name="user_settings",
    ),
]

urlpatterns += [
    optional_slash_path("fcm_relay", FCMRelayView.as_view(), name="fcm_relay"),
]
