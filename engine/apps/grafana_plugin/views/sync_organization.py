from contextlib import suppress

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.permissions import PluginTokenVerified
from apps.user_management.models import Organization
from apps.user_management.sync import sync_organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class SyncOrganizationView(GrafanaHeadersMixin, APIView):
    permission_classes = (PluginTokenVerified,)

    def post(self, request: Request) -> Response:
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]

        with suppress(Organization.DoesNotExist):
            organization = Organization.objects.get(stack_id=stack_id, org_id=org_id)
            sync_organization(organization)

        return Response(status=status.HTTP_200_OK)
