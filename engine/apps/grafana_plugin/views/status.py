import logging

from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import BasePluginAuthentication
from apps.base.models import DynamicSetting
from apps.grafana_plugin.tasks.sync import plugin_sync_organization_async
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Organization
from common.api_helpers.mixins import GrafanaHeadersMixin
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class StatusView(GrafanaHeadersMixin, APIView):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        BasePluginAuthentication,
    )

    def post(self, request: Request) -> Response:
        logger.info(
            f"authenticated via {type(request.successful_authenticator)}, user=[{request.user}] "
            f"org=[{request.auth.organization.stack_slug if request.auth.organization else None}]"
        )

        """
        Called asynchronously on each start of the plugin
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

        organization = request.auth.organization
        is_installed = False
        token_ok = False
        allow_signup = True
        api_url = create_engine_url("")

        # Check if organization is in OnCall database
        if organization:
            is_installed = True
            token_ok = organization.api_token_status == Organization.API_TOKEN_STATUS_OK
            logger.info(
                f"Status - check token org={organization.pk} status={organization.api_token_status} "
                f"token_ok={token_ok}"
            )
            if organization.is_moved:
                logger.info(f"Organization Moved! org={organization.pk}")
                api_url = create_engine_url("", override_base=organization.migration_destination.oncall_backend_url)
        else:
            allow_signup = DynamicSetting.objects.get_or_create(
                name="allow_plugin_organization_signup", defaults={"boolean_value": True}
            )[0].boolean_value

        # If user is not present in OnCall database, set token_ok to False, which will trigger reinstall
        if not request.user:
            logger.info(f"Status - user not found org={organization.pk} " f"setting token_status to PENDING")
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
                "is_user_anonymous": self.grafana_context["IsAnonymous"]
                if self.grafana_context
                else request.user is None,
                "license": settings.LICENSE,
                "version": settings.VERSION,
                "recaptcha_site_key": settings.RECAPTCHA_V3_SITE_KEY,
                "currently_undergoing_maintenance_message": settings.CURRENTLY_UNDERGOING_MAINTENANCE_MESSAGE,
                "api_url": api_url,
            }
        )
