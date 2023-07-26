from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.user_management.models.organization import Organization
from apps.user_management.sync import sync_organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class SelfHostedInstallView(GrafanaHeadersMixin, APIView):
    def post(self, _request: Request) -> Response:
        """
        We've already validated that settings.GRAFANA_API_URL is set (in apps.grafana_plugin.GrafanaPluginConfig)
        The user is now trying to finish plugin installation. We'll take the Grafana API url that they specified +
        the token that we are provided and first verify them. If all is good, upsert the organization in the database,
        and provision the plugin.
        """
        stack_id = settings.SELF_HOSTED_SETTINGS["STACK_ID"]
        org_id = settings.SELF_HOSTED_SETTINGS["ORG_ID"]
        grafana_url = settings.SELF_HOSTED_SETTINGS["GRAFANA_API_URL"]
        grafana_api_token = self.instance_context["grafana_token"]

        provisioning_info = {"error": None}

        if settings.LICENSE != settings.OPEN_SOURCE_LICENSE_NAME:
            provisioning_info["error"] = "License type not authorized"
            return Response(status=status.HTTP_403_FORBIDDEN)

        grafana_api_client = GrafanaAPIClient(api_url=grafana_url, api_token=grafana_api_token)
        _, client_status = grafana_api_client.check_token()
        status_code = client_status["status_code"]

        if status_code == status.HTTP_404_NOT_FOUND:
            provisioning_info["error"] = f"Unable to connect to the specified Grafana API - {grafana_url}"
            return Response(data=provisioning_info, status=status.HTTP_400_BAD_REQUEST)
        elif status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
            provisioning_info[
                "error"
            ] = f"You are not authorized to communicate with the specified Grafana API - {grafana_url}"
            return Response(data=provisioning_info, status=status.HTTP_400_BAD_REQUEST)

        organization = Organization.objects.filter(stack_id=stack_id, org_id=org_id).first()
        rbac_is_enabled = grafana_api_client.is_rbac_enabled_for_organization()

        if organization:
            organization.revoke_plugin()
            organization.grafana_url = grafana_url
            organization.api_token = grafana_api_token
            organization.is_rbac_permissions_enabled = rbac_is_enabled
            organization.save(update_fields=["grafana_url", "api_token", "is_rbac_permissions_enabled"])
        else:
            organization = Organization.objects.create(
                stack_id=stack_id,
                stack_slug=settings.SELF_HOSTED_SETTINGS["STACK_SLUG"],
                org_id=org_id,
                org_slug=settings.SELF_HOSTED_SETTINGS["ORG_SLUG"],
                org_title=settings.SELF_HOSTED_SETTINGS["ORG_TITLE"],
                region_slug=settings.SELF_HOSTED_SETTINGS["REGION_SLUG"],
                cluster_slug=settings.SELF_HOSTED_SETTINGS["CLUSTER_SLUG"],
                grafana_url=grafana_url,
                api_token=grafana_api_token,
                is_rbac_permissions_enabled=rbac_is_enabled,
            )

        sync_organization(organization)
        provisioning_info.update(organization.provision_plugin())

        return Response(data=provisioning_info, status=status.HTTP_201_CREATED)
