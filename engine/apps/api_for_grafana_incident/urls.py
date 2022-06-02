from django.urls import include, path

from common.api_helpers.optional_slash_router import OptionalSlashRouter

from . import views

app_name = "api_for_grafana_incident"


router = OptionalSlashRouter()

router.register(r"alert-groups", views.AlertGroupsView, basename="alert-groups")


urlpatterns = [
    path("", include(router.urls)),
]
