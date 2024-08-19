from django.urls import re_path

from apps.grafana_plugin.views import (
    InstallV2View,
    InstallView,
    RecaptchaView,
    SelfHostedInstallView,
    StatusV2View,
    StatusView,
    SyncOrganizationView,
    SyncV2View,
)

app_name = "grafana-plugin"

urlpatterns = [
    re_path(r"v2/sync/?", SyncV2View().as_view(), name="sync-v2"),
    re_path(r"v2/status/?", StatusV2View().as_view(), name="status-v2"),
    re_path(r"v2/install/?", InstallV2View().as_view(), name="install-v2"),
    re_path(r"self-hosted/install/?", SelfHostedInstallView().as_view(), name="self-hosted-install"),
    re_path(r"status/?", StatusView().as_view(), name="status"),
    re_path(r"install/?", InstallView().as_view(), name="install"),
    re_path(r"sync_organization/?", SyncOrganizationView().as_view(), name="sync-organization"),
    re_path(r"recaptcha/?", RecaptchaView().as_view(), name="recaptcha"),
]
