import logging

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import BasePluginAuthentication
from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from common.api_helpers.mixins import GrafanaHeadersMixin
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class StatusV2View(GrafanaHeadersMixin, APIView):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        BasePluginAuthentication,
    )

    def get(self, request: Request) -> Response:
        # Check if the plugin is currently undergoing maintenance, and return response without querying db
        if settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE:
            return Response(
                data={
                    "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                }
            )

        organization = request.auth.organization
        api_url = create_engine_url("")

        # If /status is called frequently this can be skipped with a cache
        grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        _, call_status = grafana_api_client.check_token()

        return Response(
            data={
                "connection_to_grafana": {
                    "url": call_status["url"],
                    "connected": call_status["connected"],
                    "status_code": call_status["status_code"],
                    "message": call_status["message"],
                },
                "license": settings.LICENSE,
                "version": settings.VERSION,
                "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                "api_url": api_url,
            }
        )
