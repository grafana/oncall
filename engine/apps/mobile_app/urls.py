from apps.mobile_app.views import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet
from common.api_helpers.optional_slash_router import OptionalSlashRouter

router = OptionalSlashRouter()

router.register("apns", APNSDeviceAuthorizedViewSet)
router.register("gcm", GCMDeviceAuthorizedViewSet)

urlpatterns = router.urls
