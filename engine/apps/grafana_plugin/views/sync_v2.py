import logging

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.serializers.sync_data import SyncDataSerializer
from apps.user_management.models import Organization
from apps.user_management.sync import apply_sync_data, get_or_create_organization
from common.api_helpers.errors import INVALID_SELF_HOSTED_ID

logger = logging.getLogger(__name__)


class SyncException(Exception):
    def __init__(self, error_data):
        self.error_data = error_data


class SyncV2View(APIView):
    def do_sync(self, request: Request) -> Organization:
        serializer = SyncDataSerializer(data=request.data)
        if not serializer.is_valid():
            raise SyncException(serializer.errors)

        sync_data = serializer.save()

        settings_stack_id = settings.SELF_HOSTED_SETTINGS["STACK_ID"]
        settings_org_id = settings.SELF_HOSTED_SETTINGS["ORG_ID"]
        if sync_data.settings.org_id != settings_org_id or sync_data.settings.stack_id != settings_stack_id:
            raise SyncException(INVALID_SELF_HOSTED_ID)

        organization = get_or_create_organization(sync_data.settings.org_id, sync_data.settings.stack_id, sync_data)
        apply_sync_data(organization, sync_data)
        return organization

    def post(self, request: Request) -> Response:
        try:
            self.do_sync(request)
        except SyncException as e:
            return Response(data=e.error_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
