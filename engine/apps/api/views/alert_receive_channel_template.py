from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.tasks import update_verbose_name_for_alert_receive_channel
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.alert_receive_channel import AlertReceiveChannelTemplatesSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log import EntityEvent, write_resource_insight_log


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
        prev_state = instance.insight_logs_serialized
        prev_web_title_template = instance.web_title_template

        result = super().update(request, *args, **kwargs)

        instance = self.get_object()
        new_state = instance.insight_logs_serialized
        new_web_title_template = instance.web_title_template

        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

        if new_web_title_template != prev_web_title_template:
            update_verbose_name_for_alert_receive_channel.delay(instance.pk)

        return result
