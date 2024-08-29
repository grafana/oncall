import gzip
import json
import logging
from dataclasses import asdict, is_dataclass

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import BasePluginAuthentication
from apps.grafana_plugin.serializers.sync_data import SyncDataSerializer
from apps.user_management.models import Organization
from apps.user_management.sync import apply_sync_data, get_or_create_organization
from common.api_helpers.errors import INVALID_SELF_HOSTED_ID

logger = logging.getLogger(__name__)


class SyncException(Exception):
    def __init__(self, error_data):
        self.error_data = error_data


class SyncV2View(APIView):
    authentication_classes = (BasePluginAuthentication,)

    def do_sync(self, request: Request) -> Organization:
        if request.headers.get("Content-Encoding") == "gzip":
            gzip_data = gzip.GzipFile(fileobj=request).read()
            decoded_data = gzip_data.decode("utf-8")
            data = json.loads(decoded_data)
        else:
            data = request.data

        serializer = SyncDataSerializer(data=data)
        if not serializer.is_valid():
            raise SyncException(serializer.errors)

        sync_data = serializer.save()

        if settings.LICENSE == settings.OPEN_SOURCE_LICENSE_NAME:
            stack_id = settings.SELF_HOSTED_SETTINGS["STACK_ID"]
            org_id = settings.SELF_HOSTED_SETTINGS["ORG_ID"]
        else:
            org_id = request.auth.organization.org_id
            stack_id = request.auth.organization.stack_id

        if sync_data.settings.org_id != org_id or sync_data.settings.stack_id != stack_id:
            raise SyncException(INVALID_SELF_HOSTED_ID)

        organization = get_or_create_organization(sync_data.settings.org_id, sync_data.settings.stack_id, sync_data)
        apply_sync_data(organization, sync_data)
        return organization

    def post(self, request: Request) -> Response:
        try:
            self.do_sync(request)
        except SyncException as e:
            return Response(
                data=asdict(e.error_data) if is_dataclass(e.error_data) else e.error_data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_200_OK)
