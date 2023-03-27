import time
from datetime import timedelta

from django.utils.functional import cached_property
from rest_framework import fields, serializers

from apps.alerts.models import CustomButton, EscalationChain, EscalationPolicy
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackUserGroup
from apps.user_management.models import User
from common.api_helpers.custom_fields import (
    CustomTimeField,
    OrganizationFilteredPrimaryKeyRelatedField,
    UsersFilteredByOrganizationField,
)
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin, OrderedModelSerializerMixin


class EscalationPolicyTypeField(fields.CharField):
    def to_representation(self, value):
        return EscalationPolicy.PUBLIC_STEP_CHOICES_MAP[value]

    def to_internal_value(self, data):
        try:
            step_type = [
                key
                for key, value in EscalationPolicy.PUBLIC_STEP_CHOICES_MAP.items()
                if value == data and key in EscalationPolicy.PUBLIC_STEP_CHOICES
            ][0]
        except IndexError:
            raise BadRequest(detail="Invalid escalation step type")
        if step_type not in EscalationPolicy.PUBLIC_STEP_CHOICES:
            raise BadRequest(detail="Invalid escalation step type")
        return step_type


class EscalationPolicySerializer(EagerLoadingMixin, OrderedModelSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=EscalationChain.objects, source="escalation_chain"
    )
    position = serializers.IntegerField(required=False, source="order")
    type = EscalationPolicyTypeField(source="step", allow_null=True)
    duration = serializers.ChoiceField(required=False, source="wait_delay", choices=EscalationPolicy.DURATION_CHOICES)
    persons_to_notify = UsersFilteredByOrganizationField(
        queryset=User.objects,
        required=False,
        source="notify_to_users_queue",
    )
    persons_to_notify_next_each_time = UsersFilteredByOrganizationField(
        queryset=User.objects,
        required=False,
        source="notify_to_users_queue",
    )
    notify_on_call_from_schedule = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=OnCallSchedule.objects, required=False, source="notify_schedule"
    )
    group_to_notify = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=SlackUserGroup.objects,
        required=False,
        source="notify_to_group",
        filter_field="slack_team_identity__organizations",
    )
    action_to_trigger = OrganizationFilteredPrimaryKeyRelatedField(
        queryset=CustomButton.objects,
        required=False,
        source="custom_button_trigger",
    )
    manual_order = serializers.BooleanField(default=False, write_only=True)
    important = serializers.BooleanField(required=False)
    notify_if_time_from = CustomTimeField(required=False, source="from_time")
    notify_if_time_to = CustomTimeField(required=False, source="to_time")

    class Meta:
        model = EscalationPolicy
        fields = [
            "id",
            "escalation_chain_id",
            "position",
            "type",
            "duration",
            "important",
            "persons_to_notify",
            "persons_to_notify_next_each_time",
            "notify_on_call_from_schedule",
            "group_to_notify",
            "action_to_trigger",
            "manual_order",
            "notify_if_time_from",
            "notify_if_time_to",
            "num_alerts_in_window",
            "num_minutes_in_window",
        ]

    PREFETCH_RELATED = ["notify_to_users_queue"]
    SELECT_RELATED = ["escalation_chain"]

    @cached_property
    def escalation_chain(self):
        if self.instance is not None:
            escalation_chain = self.instance.escalation_chain
        else:
            escalation_chain = EscalationChain.objects.get(public_primary_key=self.initial_data["escalation_chain_id"])
        return escalation_chain

    def validate_type(self, step_type):
        organization = self.context["request"].auth.organization

        if step_type == EscalationPolicy.STEP_FINAL_NOTIFYALL and organization.slack_team_identity is None:
            raise BadRequest(detail="Invalid escalation step type: step is Slack-specific")

        return step_type

    def validate_action_to_trigger(self, action_to_trigger):
        if action_to_trigger.team != self.escalation_chain.team:
            raise BadRequest(detail="Action must be assigned to the same team as the escalation chain")

        return action_to_trigger

    def validate_notify_on_call_from_schedule(self, schedule):
        if schedule.team != self.escalation_chain.team:
            raise BadRequest(detail="Schedule must be assigned to the same team as the escalation chain")

        return schedule

    def create(self, validated_data):
        validated_data = self._correct_validated_data(validated_data)
        manual_order = validated_data.pop("manual_order")
        if not manual_order:
            order = validated_data.pop("order", None)
            escalation_chain_id = validated_data.get("escalation_chain")
            # validate 'order' value before creation
            self._validate_order(order, {"escalation_chain_id": escalation_chain_id})

            instance = super().create(validated_data)
            self._change_position(order, instance)
        else:
            # validate will raise if there is a duplicated order
            self._validate_manual_order(None, validated_data)
            instance = super().create(validated_data)

        return instance

    def to_representation(self, instance):
        step = instance.step
        result = super().to_representation(instance)
        result = self._get_field_to_represent(step, result)
        if "duration" in result and result["duration"] is not None:
            result["duration"] = result["duration"].seconds
        return result

    def to_internal_value(self, data):
        if data.get("duration", None):
            try:
                time.strptime(data["duration"], "%H:%M:%S")
            except (ValueError, TypeError):
                try:
                    data["duration"] = str(timedelta(seconds=data["duration"]))
                except (ValueError, TypeError):
                    raise BadRequest(detail="Invalid duration format")
        if data.get("persons_to_notify", []) is None:  # terraform case
            data["persons_to_notify"] = []
        if data.get("persons_to_notify_next_each_time", []) is None:  # terraform case
            data["persons_to_notify_next_each_time"] = []
        return super().to_internal_value(data)

    def _get_field_to_represent(self, step, result):
        fields_to_remove = [
            "duration",
            "persons_to_notify",
            "persons_to_notify_next_each_time",
            "notify_on_call_from_schedule",
            "group_to_notify",
            "important",
            "action_to_trigger",
            "notify_if_time_from",
            "notify_if_time_to",
            "num_alerts_in_window",
            "num_minutes_in_window",
        ]
        if step == EscalationPolicy.STEP_WAIT:
            fields_to_remove.remove("duration")
        elif step in [EscalationPolicy.STEP_NOTIFY_SCHEDULE, EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT]:
            fields_to_remove.remove("notify_on_call_from_schedule")
        elif step in [
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
        ]:
            fields_to_remove.remove("persons_to_notify")
        elif step == EscalationPolicy.STEP_NOTIFY_USERS_QUEUE:
            fields_to_remove.remove("persons_to_notify_next_each_time")
        elif step in [EscalationPolicy.STEP_NOTIFY_GROUP, EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT]:
            fields_to_remove.remove("group_to_notify")
        elif step == EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
            fields_to_remove.remove("action_to_trigger")
        elif step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
            fields_to_remove.remove("notify_if_time_from")
            fields_to_remove.remove("notify_if_time_to")
        elif step == EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
            fields_to_remove.remove("num_alerts_in_window")
            fields_to_remove.remove("num_minutes_in_window")

        if (
            step in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING
            or step in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING.values()
        ):
            fields_to_remove.remove("important")
            result["important"] = step not in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING
        for field in fields_to_remove:
            result.pop(field, None)
        return result

    def _validate_manual_order(self, instance, validated_data):
        order = validated_data.get("order")
        if order is None:
            return

        policies_with_order = self.escalation_chain.escalation_policies.filter(order=order)
        if instance and instance.id:
            policies_with_order = policies_with_order.exclude(id=instance.id)

        if policies_with_order.exists():
            raise BadRequest(detail="Steps cannot have duplicated positions")

    def _correct_validated_data(self, validated_data):
        validated_data_fields_to_remove = [
            "notify_to_users_queue",
            "wait_delay",
            "notify_schedule",
            "notify_to_group",
            "custom_button_trigger",
            "from_time",
            "to_time",
            "num_alerts_in_window",
            "num_minutes_in_window",
        ]
        step = validated_data.get("step")
        important = validated_data.pop("important", None)

        if step in [EscalationPolicy.STEP_NOTIFY_SCHEDULE, EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT]:
            validated_data_fields_to_remove.remove("notify_schedule")
        elif step == EscalationPolicy.STEP_WAIT:
            validated_data_fields_to_remove.remove("wait_delay")
        elif step in [
            EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
            EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
        ]:
            validated_data_fields_to_remove.remove("notify_to_users_queue")
        elif step in [EscalationPolicy.STEP_NOTIFY_GROUP, EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT]:
            validated_data_fields_to_remove.remove("notify_to_group")
        elif step == EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
            validated_data_fields_to_remove.remove("custom_button_trigger")
        elif step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
            validated_data_fields_to_remove.remove("from_time")
            validated_data_fields_to_remove.remove("to_time")
        elif step == EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
            validated_data_fields_to_remove.remove("num_alerts_in_window")
            validated_data_fields_to_remove.remove("num_minutes_in_window")

        for field in validated_data_fields_to_remove:
            validated_data.pop(field, None)

        if step in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING and important:
            validated_data["step"] = EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING[step]
        elif step in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING.values() and important is False:
            validated_data["step"] = [
                key for key, value in EscalationPolicy.DEFAULT_TO_IMPORTANT_STEP_MAPPING.items() if value == step
            ][0]
        return validated_data


class EscalationPolicyUpdateSerializer(EscalationPolicySerializer):
    escalation_chain_id = OrganizationFilteredPrimaryKeyRelatedField(read_only=True, source="escalation_chain")
    type = EscalationPolicyTypeField(required=False, source="step", allow_null=True)

    class Meta(EscalationPolicySerializer.Meta):
        read_only_fields = ("route_id",)

    def update(self, instance, validated_data):
        if "step" in validated_data:
            step = validated_data["step"]
        else:
            step = instance.step

        validated_data["step"] = step
        validated_data = self._correct_validated_data(validated_data)

        if step != instance.step:
            if step is not None:
                if step not in [EscalationPolicy.STEP_NOTIFY_SCHEDULE, EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT]:
                    instance.notify_schedule = None
                if step != EscalationPolicy.STEP_WAIT:
                    instance.wait_delay = None
                if step not in [
                    EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
                    EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
                    EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS_IMPORTANT,
                ]:
                    instance.notify_to_users_queue.clear()
                if step not in [EscalationPolicy.STEP_NOTIFY_GROUP, EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT]:
                    instance.notify_to_group = None
                if step != EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON:
                    instance.custom_button_trigger = None
                if step != EscalationPolicy.STEP_NOTIFY_IF_TIME:
                    instance.from_time = None
                    instance.to_time = None
                if step != EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
                    instance.num_alerts_in_window = None
                    instance.num_minutes_in_window = None

        manual_order = validated_data.pop("manual_order")

        if not manual_order:
            order = validated_data.pop("order", None)
            self._validate_order(order, {"escalation_chain_id": instance.escalation_chain_id})
            self._change_position(order, instance)
        else:
            # validate will raise if there is a duplicated order
            self._validate_manual_order(instance, validated_data)

        return super().update(instance, validated_data)
