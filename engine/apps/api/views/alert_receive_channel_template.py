from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.alert_receive_channel import AlertReceiveChannelTemplatesSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class AlertReceiveChannelTemplateView(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdmin: MODIFY_ACTIONS,
        AnyRole: READ_ACTIONS,
    }

    model = AlertReceiveChannel
    serializer_class = AlertReceiveChannelTemplatesSerializer

    def get_queryset(self):
        queryset = AlertReceiveChannel.objects.filter(
            organization=self.request.auth.organization,
            team=self.request.user.current_team,
        )
        return queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_state = instance.repr_settings_for_client_side_logging
        result = super().update(request, *args, **kwargs)
        instance = self.get_object()
        new_state = instance.repr_settings_for_client_side_logging

        if new_state != old_state:
            description = f"Integration settings was changed from:\n{old_state}\nto:\n{new_state}"
            create_organization_log(
                instance.organization,
                self.request.user,
                OrganizationLogType.TYPE_INTEGRATION_CHANGED,
                description,
            )

        return result
