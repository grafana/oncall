from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import AnyRole, IsAdmin, MethodPermission
from apps.api.serializers.organization_slack_settings import OrganizationSlackSettingsSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.models import Organization
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log


class SlackTeamSettingsAPIView(views.APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, MethodPermission)

    method_permissions = {
        IsAdmin: ("PUT",),
        AnyRole: ("GET",),
    }

    serializer_class = OrganizationSlackSettingsSerializer

    def get(self, request):
        organization = self.request.auth.organization
        serializer = self.serializer_class(organization)
        return Response(serializer.data)

    def put(self, request):
        organization = self.request.auth.organization
        old_state = organization.repr_settings_for_client_side_logging
        serializer = self.serializer_class(organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        description = f"Organization settings was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            organization, request.user, OrganizationLogType.TYPE_ORGANIZATION_SETTINGS_CHANGED, description
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
