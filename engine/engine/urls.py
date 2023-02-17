"""engine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import HealthCheckView, ReadinessCheckView, StartupProbeView

urlpatterns = [
    path("", HealthCheckView.as_view()),
    path("health/", HealthCheckView.as_view()),
    path("ready/", ReadinessCheckView.as_view()),
    path("startupprobe/", StartupProbeView.as_view()),
    # path('slow/', SlowView.as_view()),
    # path('exception/', ExceptionView.as_view()),
    path(settings.ONCALL_DJANGO_ADMIN_PATH, admin.site.urls),
    path("api/gi/v1/", include("apps.api_for_grafana_incident.urls", namespace="api-gi")),
    path("api/internal/v1/", include("apps.api.urls", namespace="api-internal")),
    path("api/internal/v1/", include("social_django.urls", namespace="social")),
    path("api/internal/v1/plugin/", include("apps.grafana_plugin.urls", namespace="grafana-plugin")),
    path("integrations/v1/", include("apps.integrations.urls", namespace="integrations")),
    path("twilioapp/", include("apps.twilioapp.urls")),
    path("api/v1/", include("apps.public_api.urls", namespace="api-public")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
    urlpatterns += [
        path("api/internal/v1/slack/", include("apps.slack.urls")),
    ]

if settings.FEATURE_TELEGRAM_INTEGRATION_ENABLED:
    urlpatterns += [path("telegram/", include("apps.telegram.urls"))]

if settings.FEATURE_SLACK_INTEGRATION_ENABLED:
    urlpatterns += [
        path("slack/", include("apps.slack.urls")),
    ]

if settings.FEATURE_MOBILE_APP_INTEGRATION_ENABLED:
    urlpatterns += [
        path("mobile_app/v1/", include("apps.mobile_app.urls", namespace="mobile_app")),
        path("api/internal/v1/mobile_app/", include("apps.mobile_app.urls", namespace="mobile_app_tmp")),
    ]


if settings.OSS_INSTALLATION:
    urlpatterns += [
        path("api/internal/v1/", include("apps.oss_installation.urls", namespace="oss_installation")),
    ]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.SILK_PROFILER_ENABLED:
    urlpatterns += [path(settings.SILK_PATH, include("silk.urls", namespace="silk"))]

admin.site.site_header = settings.ADMIN_SITE_HEADER
