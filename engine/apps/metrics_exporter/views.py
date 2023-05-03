from django.conf import settings
from django.http import Http404, HttpResponse
from prometheus_client import generate_latest
from rest_framework.views import APIView

from .metrics_collectors import application_metrics_registry


def is_internal(request):
    return request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS


class MetricsExporterView(APIView):
    def get(self, request):
        # todo:metrics
        if not is_internal(request):
            raise Http404

        result = generate_latest(application_metrics_registry).decode("utf-8")
        return HttpResponse(result, content_type="text/plain; version=0.0.4; charset=utf-8")
