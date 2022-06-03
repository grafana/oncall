from django.apps import apps
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.grafana_plugin.permissions import PluginTokenVerified
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class StatusView(GrafanaHeadersMixin, APIView):
    permission_classes = (PluginTokenVerified,)

    def get(self, request: Request) -> Response:
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]
        is_installed = False
        connected_to_grafana = False
        token_ok = False
        allow_signup = True
        organization = Organization.objects.filter(stack_id=stack_id, org_id=org_id).first()
        if organization:
            is_installed = True
            client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
            token_info, client_status = client.check_token()
            connected_to_grafana = (
                client_status["connected"]
                or client_status["status_code"] == status.HTTP_401_UNAUTHORIZED
                or client_status["status_code"] == status.HTTP_403_FORBIDDEN
            )
            if token_info:
                token_ok = True
        else:
            DynamicSetting = apps.get_model("base", "DynamicSetting")
            allow_signup = DynamicSetting.objects.get_or_create(
                name="allow_plugin_organization_signup", defaults={"boolean_value": True}
            )[0].boolean_value

        return Response(
            data={
                "is_installed": is_installed,
                "grafana_connection_ok": connected_to_grafana,
                "token_ok": token_ok,
                "allow_signup": allow_signup,
                "is_user_anonymous": self.grafana_context["IsAnonymous"],
                "license": settings.LICENSE,
                "version": settings.VERSION,
            }
        )
