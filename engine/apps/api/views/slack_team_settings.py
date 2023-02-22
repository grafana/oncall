from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.api.serializers.organization_slack_settings import OrganizationSlackSettingsSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.models import Organization
from common.insight_log import EntityEvent, write_resource_insight_log


class SlackTeamSettingsAPIView(views.APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": [RBACPermission.Permissions.CHATOPS_READ],
        "put": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    serializer_class = OrganizationSlackSettingsSerializer

    def get(self, request):
        organization = self.request.auth.organization
        serializer = self.serializer_class(organization)
        return Response(serializer.data)

    def put(self, request):
        organization = self.request.auth.organization
        prev_state = organization.insight_logs_serialized
        serializer = self.serializer_class(organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )
        return Response(serializer.data)


class AcknowledgeReminderOptionsAPIView(views.APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        choices = []
        for item in Organization.ACKNOWLEDGE_REMIND_CHOICES:
            choices.append(
                {"value": item[0], "sec_value": Organization.ACKNOWLEDGE_REMIND_DELAY[item[0]], "display_name": item[1]}
            )
        return Response(choices)


class UnAcknowledgeTimeoutOptionsAPIView(views.APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        choices = []
        for item in Organization.UNACKNOWLEDGE_TIMEOUT_CHOICES:
            choices.append(
                {
                    "value": item[0],
                    "sec_value": Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[item[0]],
                    "display_name": item[1],
                }
            )
        return Response(choices)
