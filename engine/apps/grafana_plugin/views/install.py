import logging

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.serializers.sync_data import SyncDataSerializer
from apps.user_management.sync import get_organization
from common.api_helpers.errors import SELF_HOSTED_ONLY_FEATURE_ERROR, INVALID_SELF_HOSTED_ID

logger = logging.getLogger(__name__)


class InstallView(APIView):

    def post(self, request: Request) -> Response:
        if settings.LICENSE != settings.OPEN_SOURCE_LICENSE_NAME:
            return Response(data=SELF_HOSTED_ONLY_FEATURE_ERROR, status=status.HTTP_403_FORBIDDEN)

        serializer = SyncDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sync_data = serializer.save()
        settings_stack_id = settings.SELF_HOSTED_SETTINGS["STACK_ID"]
        settings_org_id = settings.SELF_HOSTED_SETTINGS["ORG_ID"]
        if(sync_data.settings.org_id != settings_org_id or sync_data.settings.stack_id != settings_stack_id):
            return Response(data=INVALID_SELF_HOSTED_ID, status=status.HTTP_400_BAD_REQUEST)

        organization = get_organization(sync_data.settings.org_id, sync_data.settings.stack_id, sync_data)
        organization.revoke_plugin()
        provisioned_data = organization.provision_plugin()
        return Response(data=provisioned_data, status=status.HTTP_200_OK)
