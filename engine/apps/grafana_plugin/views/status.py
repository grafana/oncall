from django.apps import apps
from django.conf import settings
from django.http import JsonResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.grafana_plugin.permissions import PluginTokenVerified
from apps.grafana_plugin.tasks.sync import plugin_sync_organization_async
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class StatusView(GrafanaHeadersMixin, APIView):
    permission_classes = (PluginTokenVerified,)

    def post(self, request: Request) -> Response:
        """
        Called asyncronounsly on each start of the plugin
        Checks if plugin is correctly installed and async runs a task
        to sync users, teams and org
        """
        # Check if the plugin is currently undergoing maintenance, and return response without querying db
        if settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE:
            return JsonResponse(
                {
                    "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                }
            )

        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]

        is_installed = False
        token_ok = False
        allow_signup = True

        # Check if organization is in OnCall database
        if organization := Organization.objects.get(stack_id=stack_id, org_id=org_id):
            is_installed = True
            # _, resp = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token).check_token()
            # token_ok = resp["connected"]
            # TODO: Consider checking from OnCall db instead of Grafana to make it faster:
            token_ok = organization.api_token_status == Organization.API_TOKEN_STATUS_OK
        else:
            DynamicSetting = apps.get_model("base", "DynamicSetting")
            allow_signup = DynamicSetting.objects.get_or_create(
                name="allow_plugin_organization_signup", defaults={"boolean_value": True}
            )[0].boolean_value

        # Check if current user is in OnCall database
        user_is_present_in_org = PluginAuthentication.is_user_from_request_present_in_organization(
            request, organization
        )
        # If user is not present in OnCall database, set token_ok to False, which will trigger reinstall
        if not user_is_present_in_org:
            token_ok = False

        # Start task to refresh organization data in OnCall database with Grafana
        plugin_sync_organization_async.apply_async((organization.pk,))

        return Response(
            data={
                "is_installed": is_installed,
                "token_ok": token_ok,
                "allow_signup": allow_signup,
                "is_user_anonymous": self.grafana_context["IsAnonymous"],
                "license": settings.LICENSE,
                "version": settings.VERSION,
                "recaptcha_site_key": settings.RECAPTCHA_V3_SITE_KEY,
                "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
            }
        )

    def get(self, _request: Request) -> Response:
        """Deprecated. May be used for the plugins with versions < 1.3.5"""
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
            DynamicSetting = apps.get_model("base", "DynamicSetting")
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
