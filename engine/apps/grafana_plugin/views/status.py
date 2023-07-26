from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.grafana_plugin.permissions import PluginTokenVerified
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class StatusView(GrafanaHeadersMixin, APIView):
    permission_classes = (PluginTokenVerified,)

    def get(self, _request: Request) -> Response:
        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]
        is_installed = False
        token_ok = False
        allow_signup = True

        if organization := Organization.objects.filter(stack_id=stack_id, org_id=org_id).first():
            is_installed = True
            _, resp = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token).check_token()
            token_ok = resp["connected"]
        else:
            from apps.base.models import DynamicSetting

            allow_signup = DynamicSetting.objects.get_or_create(
                name="allow_plugin_organization_signup", defaults={"boolean_value": True}
            )[0].boolean_value

        return Response(
            data={
                "is_installed": is_installed,
                "token_ok": token_ok,
                "allow_signup": allow_signup,
                "is_user_anonymous": self.grafana_context["IsAnonymous"],
                "license": settings.LICENSE,
                "version": settings.VERSION,
            }
        )
