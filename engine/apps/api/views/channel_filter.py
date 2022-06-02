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
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import CreateSerializerMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin
from common.exceptions import UnableToSendDemoAlert


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
        user = request.user
        instance = self.get_object()
        if instance.is_default:
            raise BadRequest(detail="Unable to delete default filter")
        else:
            alert_receive_channel = instance.alert_receive_channel
            route_verbal = instance.verbal_name_for_clients.capitalize()
            description = f"{route_verbal} for integration {alert_receive_channel.verbal_name} was deleted"
            create_organization_log(
                user.organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_DELETED, description
            )
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save()
        instance = serializer.instance
        alert_receive_channel = instance.alert_receive_channel
        route_verbal = instance.verbal_name_for_clients.capitalize()
        description = f"{route_verbal} was created for integration {alert_receive_channel.verbal_name}"
        create_organization_log(user.organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_CREATED, description)

    def perform_update(self, serializer):
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        alert_receive_channel = serializer.instance.alert_receive_channel
        route_verbal = serializer.instance.verbal_name_for_clients
        description = (
            f"Settings for {route_verbal} of integration {alert_receive_channel.verbal_name} "
            f"was changed from:\n{old_state}\nto:\n{new_state}"
        )
        create_organization_log(user.organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_CHANGED, description)

    @action(detail=True, methods=["put"])
    def move_to_position(self, request, pk):
        position = request.query_params.get("position", None)
        if position is not None:
            try:
                source_filter = ChannelFilter.objects.get(public_primary_key=pk)
            except ChannelFilter.DoesNotExist:
                raise BadRequest(detail="Channel filter does not exist")
            try:
                if source_filter.is_default:
                    raise BadRequest(detail="Unable to change position for default filter")
                user = self.request.user
                old_state = source_filter.repr_settings_for_client_side_logging

                source_filter.to(int(position))

                new_state = source_filter.repr_settings_for_client_side_logging
                alert_receive_channel = source_filter.alert_receive_channel
                route_verbal = source_filter.verbal_name_for_clients
                description = (
                    f"Settings for {route_verbal} of integration {alert_receive_channel.verbal_name} "
                    f"was changed from:\n{old_state}\nto:\n{new_state}"
                )
                create_organization_log(
                    user.organization,
                    user,
                    OrganizationLogType.TYPE_CHANNEL_FILTER_CHANGED,
                    description,
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
