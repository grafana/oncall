from datetime import timedelta

from rest_framework import serializers

from apps.alerts.models import EscalationChain, EscalationPolicy
from apps.alerts.utils import is_declare_incident_step_enabled
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackUserGroup
from apps.user_management.models import Team, User
from apps.webhooks.models import Webhook
from common.api_helpers.custom_fields import (
    DurationSecondsField,
    OrganizationFilteredPrimaryKeyRelatedField,
    UsersFilteredByOrganizationField,
)
from common.api_helpers.mixins import EagerLoadingMixin

WAIT_DELAY = "wait_delay"
NOTIFY_SCHEDULE = "notify_schedule"
NOTIFY_TO_USERS_QUEUE = "notify_to_users_queue"
NOTIFY_GROUP = "notify_to_group"
NOTIFY_TEAM_MEMBERS = "notify_to_team_members"
FROM_TIME = "from_time"
TO_TIME = "to_time"
NUM_ALERTS_IN_WINDOW = "num_alerts_in_window"
NUM_MINUTES_IN_WINDOW = "num_minutes_in_window"
CUSTOM_WEBHOOK_TRIGGER = "custom_webhook"
SEVERITY = "severity"

STEP_TYPE_TO_RELATED_FIELD_MAP = {
    EscalationPolicy.STEP_WAIT: [WAIT_DELAY],
    EscalationPolicy.STEP_NOTIFY_SCHEDULE: [NOTIFY_SCHEDULE],
    EscalationPolicy.STEP_NOTIFY_USERS_QUEUE: [NOTIFY_TO_USERS_QUEUE],
    EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS: [NOTIFY_TO_USERS_QUEUE],
    EscalationPolicy.STEP_NOTIFY_GROUP: [NOTIFY_GROUP],
    EscalationPolicy.STEP_NOTIFY_TEAM_MEMBERS: [NOTIFY_TEAM_MEMBERS],
    EscalationPolicy.STEP_NOTIFY_IF_TIME: [FROM_TIME, TO_TIME],
    EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW: [NUM_ALERTS_IN_WINDOW, NUM_MINUTES_IN_WINDOW],
    EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK: [CUSTOM_WEBHOOK_TRIGGER],
    EscalationPolicy.STEP_DECLARE_INCIDENT: [SEVERITY],
}


class EscalationPolicySerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    escalation_chain = OrganizationFilteredPrimaryKeyRelatedField(queryset=EscalationChain.objects)
    important = serializers.BooleanField(required=False)

    notify_to_users_queue = UsersFilteredByOrganizationField(
        queryset=User.objects,
        required=False,
    )
    wait_delay = DurationSecondsField(
        required=False,
        allow_null=True,
        min_value=timedelta(minutes=1),
        max_value=timedelta(hours=24),
    )
    num_minutes_in_window = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,  # 1 minute
        max_value=24 * 60,  # 24 hours
    )
    notify_schedule = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=OnCallSchedule.objects,
        required=False,
        allow_null=True,
    )
    notify_to_team_members = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=Team.objects,
        required=False,
        allow_null=True,
    )
    notify_to_group = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=SlackUserGroup.objects,
        required=False,
        allow_null=True,
        filter_field="slack_team_identity__organizations",
    )
    custom_webhook = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=Webhook.objects,
        required=False,
        allow_null=True,
        filter_field="organization",
    )
    severity = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = EscalationPolicy
        fields = [
            "id",
            "step",
            "wait_delay",
            "escalation_chain",
            "notify_to_users_queue",
            "from_time",
            "to_time",
            "num_alerts_in_window",
            "num_minutes_in_window",
            "slack_integration_required",
            "custom_webhook",
            "notify_schedule",
            "notify_to_group",
            "notify_to_team_members",
            "severity",
            "important",
        ]

    SELECT_RELATED = [
        "escalation_chain",
        "notify_schedule",
        "notify_to_group",
        "notify_to_team_members",
        "custom_webhook",
    ]
    PREFETCH_RELATED = ["notify_to_users_queue"]

    def validate(self, data):
        fields_to_check = [
            WAIT_DELAY,
            NOTIFY_SCHEDULE,
            NOTIFY_TO_USERS_QUEUE,
            NOTIFY_TEAM_MEMBERS,
            NOTIFY_GROUP,
            FROM_TIME,
            TO_TIME,
            NUM_ALERTS_IN_WINDOW,
            NUM_MINUTES_IN_WINDOW,
            CUSTOM_WEBHOOK_TRIGGER,
            SEVERITY,
        ]

        step = data.get("step")
        if step is None:
            raise serializers.ValidationError({"step": "This field is required."})

        if data.get("important") and step in EscalationPolicy.STEPS_WITH_NO_IMPORTANT_VERSION_SET:
            raise serializers.ValidationError(f"Step {step} can't be important")

        for f in STEP_TYPE_TO_RELATED_FIELD_MAP.get(step, []):
            fields_to_check.remove(f)

        for field in fields_to_check:
            if field == NOTIFY_TO_USERS_QUEUE:
                # notify_to_users queue is m-to-m relation so we use empty list instead of None
                if len(data.get(field, [])) != 0:
                    raise serializers.ValidationError(f"Invalid combination if step {step} and {field}")
            else:
                if data.get(field, None) is not None:
                    raise serializers.ValidationError(f"Invalid combination if step {step} and {field}")
        return data

    def validate_step(self, step_type):
        organization = self.context["request"].user.organization
        if step_type not in EscalationPolicy.INTERNAL_API_STEPS:
            raise serializers.ValidationError("Invalid step value")
        if step_type in EscalationPolicy.SLACK_INTEGRATION_REQUIRED_STEPS and organization.slack_team_identity is None:
            raise serializers.ValidationError("Invalid escalation step type: step is Slack-specific")
        if step_type == EscalationPolicy.STEP_DECLARE_INCIDENT and not is_declare_incident_step_enabled(organization):
            raise serializers.ValidationError("Invalid escalation step type: step is not enabled")
        return step_type

    def to_representation(self, instance):
        step = instance.step
        result = super().to_representation(instance)
        result = EscalationPolicySerializer._get_important_field(step, result)
        return result

    @staticmethod
    def _get_important_field(step, result):
        if step in {*EscalationPolicy.DEFAULT_STEPS_SET, *EscalationPolicy.STEPS_WITH_NO_IMPORTANT_VERSION_SET}:
            result["important"] = False
        elif step in EscalationPolicy.IMPORTANT_STEPS_SET:
            result["important"] = True
            result["step"] = EscalationPolicy.IMPORTANT_TO_DEFAULT_STEP_MAPPING[step]
        return result

    @staticmethod
    def _convert_to_important_step_if_needed(validated_data):
        step = validated_data.get("step")
        important = validated_data.pop("important", None)

        if step in EscalationPolicy.DEFAULT_STEPS_SET and important:
            validated_data["step"] = EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING[step]

        return validated_data


class EscalationPolicyCreateSerializer(EscalationPolicySerializer):
    class Meta(EscalationPolicySerializer.Meta):
        extra_kwargs = {"escalation_chain": {"required": True, "allow_null": False}}

    def create(self, validated_data):
        validated_data = EscalationPolicyCreateSerializer._convert_to_important_step_if_needed(validated_data)
        instance = super().create(validated_data)
        return instance


class EscalationPolicyUpdateSerializer(EscalationPolicySerializer):
    escalation_chain = serializers.CharField(read_only=True, source="escalation_chain.public_primary_key")

    class Meta(EscalationPolicySerializer.Meta):
        read_only_fields = ["escalation_chain"]

    def update(self, instance, validated_data):
        step = validated_data.get("step", instance.step)
        validated_data = EscalationPolicyUpdateSerializer._drop_not_step_type_related_fields(step, validated_data)
        validated_data = EscalationPolicyUpdateSerializer._convert_to_important_step_if_needed(validated_data)
        return super().update(instance, validated_data)

    @staticmethod
    def _drop_not_step_type_related_fields(step, validated_data):
        fields_to_set_none = [
            WAIT_DELAY,
            NOTIFY_SCHEDULE,
            NOTIFY_TO_USERS_QUEUE,
            NOTIFY_GROUP,
            NOTIFY_TEAM_MEMBERS,
            FROM_TIME,
            TO_TIME,
            NUM_ALERTS_IN_WINDOW,
            NUM_MINUTES_IN_WINDOW,
            CUSTOM_WEBHOOK_TRIGGER,
            SEVERITY,
        ]

        for f in STEP_TYPE_TO_RELATED_FIELD_MAP.get(step, []):
            fields_to_set_none.remove(f)

        for f in fields_to_set_none:
            if f == NOTIFY_TO_USERS_QUEUE:
                # notify_to_users queue is m-to-m relation so we use empty list instead of None
                validated_data[f] = []
            else:
                validated_data[f] = None

        return validated_data
