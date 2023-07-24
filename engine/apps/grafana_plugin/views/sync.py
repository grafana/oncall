import logging

from django.apps import apps
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.grafana_plugin.permissions import PluginTokenVerified
from apps.grafana_plugin.tasks.sync import plugin_sync_organization_async
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin

logger = logging.getLogger(__name__)


class PluginSyncView(GrafanaHeadersMixin, APIView):
    permission_classes = (PluginTokenVerified,)

    def post(self, request: Request) -> Response:
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]
        is_installed = False
        allow_signup = True

        try:
            # Check if organization is in OnCall database
            organization = Organization.objects.get(stack_id=stack_id, org_id=org_id)
            if organization.api_token_status == Organization.API_TOKEN_STATUS_OK:
                is_installed = True

            user_is_present_in_org = PluginAuthentication.is_user_from_request_present_in_organization(
                request, organization
            )
            if not user_is_present_in_org:
                organization.api_token_status = Organization.API_TOKEN_STATUS_PENDING
                organization.save(update_fields=["api_token_status"])

            if not organization:
                DynamicSetting = apps.get_model("base", "DynamicSetting")
                allow_signup = DynamicSetting.objects.get_or_create(
                    name="allow_plugin_organization_signup", defaults={"boolean_value": True}
                )[0].boolean_value

            plugin_sync_organization_async.apply_async((organization.pk,))
        except Organization.DoesNotExist:
            logger.info(f"Organization for stack {stack_id} org {org_id} was not found")

        return Response(
            status=status.HTTP_202_ACCEPTED,
            data={
                "is_installed": is_installed,
                "is_user_anonymous": self.grafana_context["IsAnonymous"],
                "allow_signup": allow_signup,
            },
        )

    def get(self, _request: Request) -> Response:
        """Deprecated"""
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]
        token_ok = False

        try:
            organization = Organization.objects.get(stack_id=stack_id, org_id=org_id)
            if organization.api_token_status == Organization.API_TOKEN_STATUS_PENDING:
                return Response(status=status.HTTP_202_ACCEPTED)
            elif organization.api_token_status == Organization.API_TOKEN_STATUS_OK:
                token_ok = True
        except Organization.DoesNotExist:
            logger.info(f"Organization for stack {stack_id} org {org_id} was not found")

        return Response(
            status=status.HTTP_200_OK,
            data={
                "token_ok": token_ok,
                "license": settings.LICENSE,
                "version": settings.VERSION,
                "recaptcha_site_key": settings.RECAPTCHA_V3_SITE_KEY,
            },
        )
