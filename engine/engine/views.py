from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.views.generic import View

from apps.integrations.mixins import AlertChannelDefiningMixin


class HealthCheckView(View):
    """
    This view is used in k8s liveness probe.
    k8s periodically makes requests to this view and
    if the requests fail the container will be restarted
    """

    dangerously_bypass_middlewares = True

    def get(self, request):
        return HttpResponse("Ok")


class ReadinessCheckView(View):
    """
    This view is used in k8s readiness probe.
    k8s periodically makes requests to this view and
    if the requests fail the container will stop getting the traffic.
    """

    dangerously_bypass_middlewares = True

    def get(self, request):
        return HttpResponse("Ok")


class StartupProbeView(View):
    """
    This view is used in k8s startup probe.
    k8s makes requests to this view on the startup and
    if the requests fail the container will be restarted
    Caching AlertReceive channels if they are not cached. Also checking initial database connection.
    """

    dangerously_bypass_middlewares = True

    def get(self, request):
        if cache.get(AlertChannelDefiningMixin.CACHE_KEY_DB_FALLBACK) is None:
            AlertChannelDefiningMixin().update_alert_receive_channel_cache()

        cache.set("healthcheck", "healthcheck", 30)  # Checking cache connectivity
        assert cache.get("healthcheck") == "healthcheck"

        return HttpResponse("Ok")


class MaintenanceModeStatusView(View):
    def get(self, _request):
        return JsonResponse(
            {
                "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
            }
        )
