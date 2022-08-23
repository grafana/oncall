from django.db.models import OuterRef, Subquery
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import ChannelFilter
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.channel_filter import (
    ChannelFilterCreateSerializer,
    ChannelFilterSerializer,
    ChannelFilterUpdateSerializer,
)
from apps.api.throttlers import DemoAlertThrottler
from apps.auth_token.auth import PluginAuthentication
from apps.slack.models import SlackChannel
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import CreateSerializerMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin
from common.exceptions import UnableToSendDemoAlert
from common.insight_log import EntityEvent, write_resource_insight_log


class ChannelFilterView(PublicPrimaryKeyMixin, CreateSerializerMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "move_to_position"),
        IsAdminOrEditor: ("send_demo_alert",),
        AnyRole: READ_ACTIONS,
    }

    model = ChannelFilter
    serializer_class = ChannelFilterSerializer
    update_serializer_class = ChannelFilterUpdateSerializer
    create_serializer_class = ChannelFilterCreateSerializer

    def get_queryset(self):
        alert_receive_channel_id = self.request.query_params.get("alert_receive_channel", None)
        lookup_kwargs = {}
        if alert_receive_channel_id:
            lookup_kwargs = {"alert_receive_channel__public_primary_key": alert_receive_channel_id}

        slack_channels_subq = SlackChannel.objects.filter(
            slack_id=OuterRef("slack_channel_id"),
            slack_team_identity=self.request.auth.organization.slack_team_identity,
        ).order_by("pk")

        queryset = ChannelFilter.objects.filter(
            **lookup_kwargs,
            alert_receive_channel__organization=self.request.auth.organization,
            alert_receive_channel__team=self.request.user.current_team,
            alert_receive_channel__deleted_at=None,
        ).annotate(
            slack_channel_name=Subquery(slack_channels_subq.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels_subq.values("public_primary_key")[:1]),
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_default:
            raise BadRequest(detail="Unable to delete default filter")
        else:
            write_resource_insight_log(
                instance=instance,
                author=self.request.user,
                event=EntityEvent.DELETED,
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    @action(detail=True, methods=["put"])
    def move_to_position(self, request, pk):
        position = request.query_params.get("position", None)
        if position is not None:
            try:
                instance = ChannelFilter.objects.get(public_primary_key=pk)
            except ChannelFilter.DoesNotExist:
                raise BadRequest(detail="Channel filter does not exist")
            try:
                if instance.is_default:
                    raise BadRequest(detail="Unable to change position for default filter")
                prev_state = instance.insight_logs_serialized
                instance.to(int(position))
                new_state = instance.insight_logs_serialized

                write_resource_insight_log(
                    instance=instance,
                    author=self.request.user,
                    event=EntityEvent.UPDATED,
                    prev_state=prev_state,
                    new_state=new_state,
                )
                return Response(status=status.HTTP_200_OK)
            except ValueError as e:
                raise BadRequest(detail=f"{e}")
        else:
            raise BadRequest(detail="Position was not provided")

    @action(detail=True, methods=["post"], throttle_classes=[DemoAlertThrottler])
    def send_demo_alert(self, request, pk):
        instance = ChannelFilter.objects.get(public_primary_key=pk)
        try:
            instance.send_demo_alert()
        except UnableToSendDemoAlert as e:
            raise BadRequest(detail=str(e))
        return Response(status=status.HTTP_200_OK)
