from django.urls import include, path

from apps.api.views.v2.alert_group import AlertGroupView
from common.api_helpers.optional_slash_router import OptionalSlashRouter

app_name = "api-v2"

router = OptionalSlashRouter()
router.register(r"alertgroups", AlertGroupView, basename="alertgroup")

urlpatterns = [
    path("", include(router.urls)),
]
