from apps.mobile_app.views import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet, MobileAppAuthTokenAPIView
from common.api_helpers.optional_slash_router import OptionalSlashRouter, optional_slash_path

app_name = "mobile_app"
router = OptionalSlashRouter()

router.register("apns", APNSDeviceAuthorizedViewSet, basename="apns")
router.register("gcm", GCMDeviceAuthorizedViewSet, basename="gcm")

urlpatterns = [
    *router.urls,
    optional_slash_path("auth_token", MobileAppAuthTokenAPIView.as_view(), name="auth_token"),
]
