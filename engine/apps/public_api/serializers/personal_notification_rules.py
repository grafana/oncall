import time
from datetime import timedelta

from rest_framework import exceptions, serializers

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import NotificationChannelPublicAPIOptions
from common.api_helpers.custom_fields import UserIdField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin
from common.ordered_model.serializer import OrderedModelSerializer


class PersonalNotificationRuleSerializer(EagerLoadingMixin, OrderedModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    user_id = UserIdField(required=True, source="user")
    type = serializers.CharField(
        required=False,
    )
    duration = serializers.ChoiceField(
        required=False, source="wait_delay", choices=UserNotificationPolicy.DURATION_CHOICES
    )

    SELECT_RELATED = ["user"]

    # Public API has fields "step" and "notify_by" combined into one step "type"
    # Step.NOTIFY is handled using NotificationChannelPublicAPIOptions class, but Step.WAIT is handled differently.
    TYPE_WAIT = "wait"

    class Meta:
        model = UserNotificationPolicy
        fields = OrderedModelSerializer.Meta.fields + ["id", "user_id", "type", "duration", "important"]

    def create(self, validated_data):
        if "type" not in validated_data:
            raise exceptions.ValidationError({"type": "Type is required"})

        validated_data = self.correct_validated_data(validated_data)
        # type is alias for combined step + notify_by field in serializer
        # correct_validated_data parse type to step + notify_by
        # that is why step key is used instead of type below
        if "wait_delay" in validated_data and validated_data["step"] != UserNotificationPolicy.Step.WAIT:
            raise exceptions.ValidationError({"duration": "Duration can't be set"})

        return super().create(validated_data)

    def to_internal_value(self, data):
        if "duration" in data:
            try:
                time.strptime(data["duration"], "%H:%M:%S")
            except (ValueError, TypeError):
                try:
                    data["duration"] = str(timedelta(seconds=data["duration"]))
                except (ValueError, TypeError):
                    raise BadRequest(detail="Invalid duration format")
        return super().to_internal_value(data)

    def to_representation(self, instance):
        step = instance.step
        result = super().to_representation(instance)

        if instance.step == UserNotificationPolicy.Step.WAIT:
            result["type"] = self.TYPE_WAIT
        else:
            result["type"] = NotificationChannelPublicAPIOptions.LABELS[instance.notify_by]

        result = self.clear_fields(step, result)

        if "duration" in result and result["duration"] is not None:
            result["duration"] = result["duration"].seconds
        return result

    # remove duration from response if step is not wait
    def clear_fields(self, step, result):
        possible_fields = ["duration"]
        if step == UserNotificationPolicy.Step.WAIT:
            possible_fields.remove("duration")
        for field in possible_fields:
            result.pop(field, None)
        return result

    def correct_validated_data(self, validated_data):
        rule_type = validated_data.get("type")
        step, notification_channel = self._type_to_step_and_notification_channel(rule_type)

        validated_data["step"] = step

        if step == UserNotificationPolicy.Step.NOTIFY:
            validated_data["notify_by"] = notification_channel

        if step == UserNotificationPolicy.Step.WAIT and "wait_delay" not in validated_data:
            validated_data["wait_delay"] = UserNotificationPolicy.FIVE_MINUTES

        validated_data.pop("type")
        return validated_data

    @classmethod
    def _type_to_step_and_notification_channel(cls, rule_type):
        if rule_type == cls.TYPE_WAIT:
            return UserNotificationPolicy.Step.WAIT, None

        for notification_channel in NotificationChannelPublicAPIOptions.AVAILABLE_FOR_USE:
            label = NotificationChannelPublicAPIOptions.LABELS[notification_channel]

            if rule_type == label:
                return UserNotificationPolicy.Step.NOTIFY, notification_channel

        raise exceptions.ValidationError({"type": "Invalid type"})


class PersonalNotificationRuleUpdateSerializer(PersonalNotificationRuleSerializer):
    user_id = UserIdField(read_only=True, source="user")
    important = serializers.BooleanField(read_only=True)

    def update(self, instance, validated_data):
        if validated_data.get("type", None):
            validated_data = self.correct_validated_data(validated_data)
            # type is alias for combined step + notify_by field in serializer
            # correct_validated_data parse type to step + notify_by
            # that is why step key is used instead of type below
            if "wait_delay" in validated_data and validated_data["step"] != UserNotificationPolicy.Step.WAIT:
                raise exceptions.ValidationError({"duration": "Duration can't be set"})
            if validated_data["step"] != UserNotificationPolicy.Step.WAIT:
                validated_data["wait_delay"] = None
        else:
            if "wait_delay" in validated_data and instance.step != UserNotificationPolicy.Step.WAIT:
                raise exceptions.ValidationError({"duration": "Duration can't be set"})

        return super().update(instance, validated_data)
