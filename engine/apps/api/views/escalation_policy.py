from django.conf import settings
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import EscalationPolicy
from apps.api.permissions import RBACPermission
from apps.api.serializers.escalation_policy import (
    EscalationPolicyCreateSerializer,
    EscalationPolicySerializer,
    EscalationPolicyUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    TeamFilteringMixin,
    UpdateSerializerMixin,
)
from common.insight_log import EntityEvent, write_resource_insight_log
from common.ordered_model.viewset import OrderedModelViewSet


class EscalationPolicyView(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin[EscalationPolicy],
    CreateSerializerMixin,
    UpdateSerializerMixin,
    OrderedModelViewSet,
):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "list": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "retrieve": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "escalation_options": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "delay_options": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "num_minutes_in_window_options": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "create": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "update": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "partial_update": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "destroy": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "move_to_position": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
    }

    model = EscalationPolicy
    serializer_class = EscalationPolicySerializer
    update_serializer_class = EscalationPolicyUpdateSerializer
    create_serializer_class = EscalationPolicyCreateSerializer

    TEAM_LOOKUP = "escalation_chain__team"

    def get_queryset(self, ignore_filtering_by_available_teams=False):
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
            Q(escalation_chain__channel_filters__alert_receive_channel__deleted_at=None),
            Q(step__in=EscalationPolicy.INTERNAL_DB_STEPS) | Q(step__isnull=True),
        ).distinct()

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

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

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

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
        # TODO: DEPRECATED, REMOVE IN A FUTURE RELEASE
        choices = []
        for item in EscalationPolicy.WEB_DURATION_CHOICES:
            choices.append({"value": str(item[0]), "sec_value": item[0], "display_name": item[1]})
        return Response(choices)

    @action(detail=False, methods=["get"])
    def num_minutes_in_window_options(self, request):
        # TODO: DEPRECATED, REMOVE IN A FUTURE RELEASE
        choices = [
            {"value": choice[0], "display_name": choice[1]} for choice in EscalationPolicy.WEB_DURATION_CHOICES_MINUTES
        ]
        return Response(choices)
