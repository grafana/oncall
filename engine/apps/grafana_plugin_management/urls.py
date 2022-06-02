from django.urls import include, path

from apps.grafana_plugin_management.views import PluginInstallationsView
from common.api_helpers.optional_slash_router import OptionalSlashRouter

app_name = "grafana-plugin-management"

router = OptionalSlashRouter()
router.register(r"plugin_installations", PluginInstallationsView, basename="plugin_installations")

urlpatterns = [
    path("", include(router.urls)),
]
