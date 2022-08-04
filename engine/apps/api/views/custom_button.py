from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import AlertGroup, CustomButton
from apps.alerts.tasks.custom_button_result import custom_button_result
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.custom_button import CustomButtonSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin


class CustomButtonView(TeamFilteringMixin, PublicPrimaryKeyMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: MODIFY_ACTIONS,
        IsAdminOrEditor: ("action",),
        AnyRole: READ_ACTIONS,
    }

    model = CustomButton
    serializer_class = CustomButtonSerializer

    def get_queryset(self):
        queryset = CustomButton.objects.filter(
            organization=self.request.auth.organization,
            team=self.request.user.current_team,
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Custom action {instance.name} was created"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        description = f"Custom action {serializer.instance.name} was changed " f"from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Custom action {instance.name} was deleted"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_DELETED, description)
        instance.delete()

    @action(detail=True, methods=["post"])
    def action(self, request, pk):
        alert_group_id = request.query_params.get("alert_group", None)
        if alert_group_id is not None:
            custom_button = self.get_object()
            try:
                alert_group = AlertGroup.unarchived_objects.get(
                    public_primary_key=alert_group_id, channel=custom_button.alert_receive_channel
                )
                custom_button_result.apply_async((custom_button.pk, alert_group.pk, self.request.user.pk))
            except AlertGroup.DoesNotExist:
                raise BadRequest(detail="AlertGroup does not exist or archived")
            return Response(status=status.HTTP_200_OK)
        else:
            raise BadRequest(detail="AlertGroup is required")
