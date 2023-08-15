from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import BasePluginAuthentication
from apps.base.models import DynamicSetting
from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.grafana_plugin.tasks.sync import plugin_sync_organization_async
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class StatusView(GrafanaHeadersMixin, APIView):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        BasePluginAuthentication,
    )

    def post(self, request: Request) -> Response:
        """
        Called asyncronounsly on each start of the plugin
        Checks if plugin is correctly installed and async runs a task
        to sync users, teams and org
        """
        # Check if the plugin is currently undergoing maintenance, and return response without querying db
        if settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE:
            return Response(
                data={
                    "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                }
            )

        stack_id = self.instance_context["stack_id"]
        org_id = self.instance_context["org_id"]

        is_installed = False
        token_ok = False
        allow_signup = True
        api_url = settings.BASE_URL

        # Check if organization is in OnCall database
        if organization := Organization.objects.get(stack_id=stack_id, org_id=org_id):
            is_installed = True
            token_ok = organization.api_token_status == Organization.API_TOKEN_STATUS_OK
            if organization.is_moved:
                api_url = organization.migration_destination.oncall_backend_url
        else:
            allow_signup = DynamicSetting.objects.get_or_create(
                name="allow_plugin_organization_signup", defaults={"boolean_value": True}
            )[0].boolean_value

        # If user is not present in OnCall database, set token_ok to False, which will trigger reinstall
        if not request.user:
            token_ok = False
            organization.api_token_status = Organization.API_TOKEN_STATUS_PENDING
            organization.save(update_fields=["api_token_status"])

        # Start task to refresh organization data in OnCall database with Grafana
        plugin_sync_organization_async.apply_async((organization.pk,))

        return Response(
            data={
                "is_installed": is_installed,
                "token_ok": token_ok,
                "allow_signup": allow_signup,
                "is_user_anonymous": self.grafana_context.get("IsAnonymous", request.user is None),
                "license": settings.LICENSE,
                "version": settings.VERSION,
                "recaptcha_site_key": settings.RECAPTCHA_V3_SITE_KEY,
                "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                "api_url": api_url,
            }
        )

    def get(self, _request: Request) -> Response:
        """Deprecated. May be used for the plugins with versions < 1.3.17"""
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
                "is_user_anonymous": self.grafana_context.get("IsAnonymous", _request.user is None),
                "license": settings.LICENSE,
                "version": settings.VERSION,
            }
        )
