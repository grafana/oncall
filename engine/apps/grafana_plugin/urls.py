from django.urls import re_path

from apps.grafana_plugin.views import (
    InstallView,
    PluginSyncView,
    SelfHostedInstallView,
    StatusView,
    SyncOrganizationView,
)

app_name = "grafana-plugin"

urlpatterns = [
    re_path(r"self-hosted/install/?", SelfHostedInstallView().as_view()),
    re_path(r"status/?", StatusView().as_view()),
    re_path(r"install/?", InstallView().as_view()),
    re_path(r"sync_organization/?", SyncOrganizationView().as_view()),
    re_path(r"sync/?", PluginSyncView().as_view()),
]
