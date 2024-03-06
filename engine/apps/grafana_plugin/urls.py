from django.urls import re_path

from apps.grafana_plugin.views import InstallView, SelfHostedInstallView, StatusView, SyncOrganizationView

app_name = "grafana-plugin"

urlpatterns = [
    re_path(r"self-hosted/install/?", SelfHostedInstallView().as_view(), name="self-hosted-install"),
    re_path(r"status/?", StatusView().as_view(), name="status"),
    re_path(r"install/?", InstallView().as_view(), name="install"),
    re_path(r"sync_organization/?", SyncOrganizationView().as_view(), name="sync-organization"),
]
