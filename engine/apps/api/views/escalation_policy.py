from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationPolicy
from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.escalation_policy import (
    EscalationPolicyCreateSerializer,
    EscalationPolicySerializer,
    EscalationPolicyUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import CreateSerializerMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin


class EscalationPolicyView(PublicPrimaryKeyMixin, CreateSerializerMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "move_to_position"),
        AnyRole: (
            *READ_ACTIONS,
            "escalation_options",
            "delay_options",
            "num_minutes_in_window_options",
        ),
    }

    model = EscalationPolicy
    serializer_class = EscalationPolicySerializer
    update_serializer_class = EscalationPolicyUpdateSerializer
    create_serializer_class = EscalationPolicyCreateSerializer

    def get_queryset(self):
        escalation_chain_id = self.request.query_params.get("escalation_chain")
        user_id = self.request.query_params.get("user")
        slack_channel_id = self.request.query_params.get("slack_channel")
        channel_filter_id = self.request.query_params.get("channel_filter")

        lookup_kwargs = {}
        if escalation_chain_id is not None:
            lookup_kwargs.update({"escalation_chain__public_primary_key": escalation_chain_id})
        if user_id is not None:
            lookup_kwargs.update({"notify_to_users_queue__public_primary_key": user_id})
        if slack_channel_id is not None:
            lookup_kwargs.update({"escalation_chain__channel_filters__slack_channel_id": slack_channel_id})
        if channel_filter_id is not None:
            lookup_kwargs.update({"escalation_chain__channel_filters__public_primary_key": channel_filter_id})

        queryset = EscalationPolicy.objects.filter(
            Q(**lookup_kwargs),
            Q(escalation_chain__organization=self.request.auth.organization),
            Q(escalation_chain__team=self.request.user.current_team),
            Q(escalation_chain__channel_filters__alert_receive_channel__deleted_at=None),
            Q(step__in=EscalationPolicy.INTERNAL_DB_STEPS) | Q(step__isnull=True),
        ).distinct()

        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        organization = self.request.user.organization
        user = self.request.user
        description = (
            f"Escalation step '{instance.step_type_verbal}' with order {instance.order} "
            f"was created for escalation chain '{instance.escalation_chain.name}'"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.user.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        escalation_chain_name = serializer.instance.escalation_chain.name

        description = (
            f"Settings for escalation step of escalation chain '{escalation_chain_name}' "
            f"was changed from:\n{old_state}\nto:\n{new_state}"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.user.organization
        user = self.request.user
        description = (
            f"Escalation step '{instance.step_type_verbal}' with order {instance.order} of "
            f"of escalation chain '{instance.escalation_chain.name}' was deleted"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_DELETED, description)
        instance.delete()

    @action(detail=True, methods=["put"])
    def move_to_position(self, request, pk):
        position = request.query_params.get("position", None)
        if position is not None:
            try:
                source_step = EscalationPolicy.objects.get(public_primary_key=pk)
            except EscalationPolicy.DoesNotExist:
                raise BadRequest(detail="Step does not exist")
            try:
                user = self.request.user
                old_state = source_step.repr_settings_for_client_side_logging

                position = int(position)
                source_step.to(position)

                new_state = source_step.repr_settings_for_client_side_logging
                escalation_chain_name = source_step.escalation_chain.name
                description = (
                    f"Settings for escalation step of escalation chain '{escalation_chain_name}' "
                    f"was changed from:\n{old_state}\nto:\n{new_state}"
                )
                create_organization_log(
                    user.organization,
                    user,
                    OrganizationLogType.TYPE_ESCALATION_STEP_CHANGED,
                    description,
                )

                return Response(status=status.HTTP_200_OK)
            except ValueError as e:
                raise BadRequest(detail=f"{e}")

        else:
            raise BadRequest(detail="Position was not provided")

    @action(detail=False, methods=["get"])
    def escalation_options(self, request):
        choices = []
        for step in EscalationPolicy.INTERNAL_API_STEPS:
            verbal = EscalationPolicy.INTERNAL_API_STEPS_TO_VERBAL_MAP[step]
            can_change_importance = (
                step in EscalationPolicy.IMPORTANT_STEPS_SET or step in EscalationPolicy.DEFAULT_STEPS_SET
            )
            slack_integration_required = step in EscalationPolicy.SLACK_INTEGRATION_REQUIRED_STEPS
            if slack_integration_required and not settings.FEATURE_SLACK_INTEGRATION_ENABLED:
                continue
            choices.append(
                {
                    "value": step,
                    "display_name": verbal[0],
                    "create_display_name": verbal[1],
                    "slack_integration_required": slack_integration_required,
                    "can_change_importance": can_change_importance,
                }
            )
        return Response(choices)

    @action(detail=False, methods=["get"])
    def delay_options(self, request):
        choices = []
        for item in EscalationPolicy.WEB_DURATION_CHOICES:
            choices.append({"value": str(item[0]), "sec_value": item[0], "display_name": item[1]})
        return Response(choices)

    @action(detail=False, methods=["get"])
    def num_minutes_in_window_options(self, request):
        choices = [
            {"value": choice[0], "display_name": choice[1]} for choice in EscalationPolicy.WEB_DURATION_CHOICES_MINUTES
        ]
        return Response(choices)
