from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import BasePluginAuthentication
from apps.user_management.models import Organization
from apps.user_management.sync import sync_organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class InstallView(GrafanaHeadersMixin, APIView):
    authentication_classes = (BasePluginAuthentication,)

    def post(self, request: Request) -> Response:
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]

        organization = Organization.objects_with_deleted.filter(stack_id=stack_id, org_id=org_id).first()
        # If we receive install request to the deleted org - just restore it.
        organization.deleted_at = None
        organization.api_token = self.instance_context["grafana_token"]
        organization.save(update_fields=["api_token", "deleted_at"])

        sync_organization(organization)
        return Response(status=status.HTTP_204_NO_CONTENT)
