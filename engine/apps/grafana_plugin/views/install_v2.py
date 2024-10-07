import logging
from dataclasses import asdict, is_dataclass

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from apps.grafana_plugin.views.sync_v2 import SyncException, SyncV2View
from common.api_helpers.errors import SELF_HOSTED_ONLY_FEATURE_ERROR

logger = logging.getLogger(__name__)


class InstallV2View(SyncV2View):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request: Request) -> Response:
        if settings.LICENSE != settings.OPEN_SOURCE_LICENSE_NAME:
            return Response(data=asdict(SELF_HOSTED_ONLY_FEATURE_ERROR), status=status.HTTP_403_FORBIDDEN)

        try:
            organization = self.do_sync(request)
        except SyncException as e:
            return Response(
                data=asdict(e.error_data) if is_dataclass(e.error_data) else e.error_data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        organization.revoke_plugin()
        provisioned_data = organization.provision_plugin()

        return Response(data=provisioned_data, status=status.HTTP_200_OK)
