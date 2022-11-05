from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.alert_receive_channel import AlertReceiveChannelTemplatesSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log import EntityEvent, write_resource_insight_log
from common.jinja_templater.apply_jinja_template import JinjaTemplateRenderException


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
        try:
            result = super().update(request, *args, **kwargs)
        except JinjaTemplateRenderException as e:
            return Response(e.fallback_message, status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        new_state = instance.insight_logs_serialized
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )
        return result
