from django.db.models import Count, Q
from emoji import emojize
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import EscalationChain
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.escalation_chain import EscalationChainListSerializer, EscalationChainSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import ListSerializerMixin, PublicPrimaryKeyMixin


class EscalationChainViewSet(PublicPrimaryKeyMixin, ListSerializerMixin, viewsets.ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "copy"),
        AnyRole: (*READ_ACTIONS, "details"),
    }

    filter_backends = [SearchFilter]
    search_fields = ("^name",)

    serializer_class = EscalationChainSerializer
    list_serializer_class = EscalationChainListSerializer

    def get_queryset(self):
        queryset = (
            EscalationChain.objects.filter(
                organization=self.request.auth.organization,
                team=self.request.user.current_team,
            )
            .annotate(
                num_integrations=Count(
                    "channel_filters__alert_receive_channel",
                    distinct=True,
                    filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
                )
            )
            .annotate(
                num_routes=Count(
                    "channel_filters",
                    distinct=True,
                    filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
                )
            )
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save()

        instance = serializer.instance
        description = f"Escalation chain {instance.name} was created"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_CREATED,
            description,
        )

    def perform_destroy(self, instance):
        instance.delete()

        description = f"Escalation chain {instance.name} was deleted"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_DELETED,
            description,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_state = instance.repr_settings_for_client_side_logging

        serializer.save()

        new_state = instance.repr_settings_for_client_side_logging
        description = f"Escalation chain {instance.name} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_CHANGED,
            description,
        )

    @action(methods=["post"], detail=True)
    def copy(self, request, pk):
        user = request.user
        name = request.data.get("name")
        if name is None:
            raise BadRequest(detail={"name": ["This field may not be null."]})
        else:
            if EscalationChain.objects.filter(organization=request.auth.organization, name=name).exists():
                raise BadRequest(detail={"name": ["Escalation chain with this name already exists."]})

        obj = self.get_object()
        copy = obj.make_copy(name)
        serializer = self.get_serializer(copy)
        description = f"Escalation chain {obj.name} was copied with new name {name}"
        create_organization_log(copy.organization, user, OrganizationLogType.TYPE_CHANNEL_FILTER_CHANGED, description)
        return Response(serializer.data)

    @action(methods=["get"], detail=True)
    def details(self, request, pk):
        obj = self.get_object()
        channel_filters = obj.channel_filters.filter(alert_receive_channel__deleted_at__isnull=True).values(
            "public_primary_key",
            "filtering_term",
            "is_default",
            "alert_receive_channel__public_primary_key",
            "alert_receive_channel__verbal_name",
        )
        data = {}
        for channel_filter in channel_filters:
            channel_filter_data = {
                "display_name": "Default Route" if channel_filter["is_default"] else channel_filter["filtering_term"],
                "id": channel_filter["public_primary_key"],
            }
            data.setdefault(
                channel_filter["alert_receive_channel__public_primary_key"],
                {
                    "id": channel_filter["alert_receive_channel__public_primary_key"],
                    "display_name": emojize(channel_filter["alert_receive_channel__verbal_name"], use_aliases=True),
                    "channel_filters": [],
                },
            )["channel_filters"].append(channel_filter_data)
        return Response(data.values())
