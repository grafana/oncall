from apps.mobile_app.views import APNSDeviceAuthorizedViewSet
from common.api_helpers.optional_slash_router import OptionalSlashRouter

router = OptionalSlashRouter()
router.register(r"apns", APNSDeviceAuthorizedViewSet)

urlpatterns = router.urls
