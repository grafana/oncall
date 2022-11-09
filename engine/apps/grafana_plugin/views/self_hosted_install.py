from django.apps import apps
from django.conf import settings
from rest_framework import status
from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.grafana_plugin.permissions import SelfHostedInvitationTokenVerified
from apps.user_management.models import Organization
from apps.user_management.sync import sync_organization
from common.api_helpers.mixins import GrafanaHeadersMixin


class SelfHostedInstallView(GrafanaHeadersMixin, APIView):
    permission_classes = (SelfHostedInvitationTokenVerified,)

    def remove_invitation_token(self, token):
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        self_hosted_settings = DynamicSetting.objects.get_or_create(
            name="self_hosted_invitations",
            defaults={
                "json_value": {
                    "keys": [],
                }
            },
        )[0]
        self_hosted_settings.json_value["keys"].remove(token)
        self_hosted_settings.save(update_fields=["json_value"])

    def post(self, request: Request) -> Response:
        token_string = get_authorization_header(request).decode()
        stack_id = settings.SELF_HOSTED_SETTINGS["STACK_ID"]
        org_id = settings.SELF_HOSTED_SETTINGS["ORG_ID"]

        organization = Organization.objects.filter(stack_id=stack_id, org_id=org_id).first()
        if organization:
            organization.revoke_plugin()
            organization.grafana_url = self.instance_context["grafana_url"]
            organization.api_token = self.instance_context["grafana_token"]
            organization.save(update_fields=["grafana_url", "api_token"])
        else:
            organization = Organization.objects.create(
                stack_id=stack_id,
                stack_slug=settings.SELF_HOSTED_SETTINGS["STACK_SLUG"],
                org_id=org_id,
                org_slug=settings.SELF_HOSTED_SETTINGS["ORG_SLUG"],
                org_title=settings.SELF_HOSTED_SETTINGS["ORG_TITLE"],
                region_slug=settings.SELF_HOSTED_SETTINGS["REGION_SLUG"],
                grafana_url=self.instance_context["grafana_url"],
                api_token=self.instance_context["grafana_token"],
            )
        sync_organization(organization)
        provisioning_info = organization.provision_plugin()
        self.remove_invitation_token(token_string)
        return Response(data=provisioning_info, status=status.HTTP_201_CREATED)
