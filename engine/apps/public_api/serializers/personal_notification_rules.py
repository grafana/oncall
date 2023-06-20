import time
from datetime import timedelta

from rest_framework import exceptions, serializers

from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import NotificationChannelPublicAPIOptions
from common.api_helpers.custom_fields import UserIdField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import EagerLoadingMixin


class PersonalNotificationRuleSerializer(EagerLoadingMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    user_id = UserIdField(required=True, source="user")
    position = serializers.IntegerField(required=False, source="order")
    type = serializers.CharField(
        required=False,
    )

    duration = serializers.ChoiceField(
        required=False, source="wait_delay", choices=UserNotificationPolicy.DURATION_CHOICES
    )
    manual_order = serializers.BooleanField(default=False, write_only=True)

    SELECT_RELATED = ["user"]

    # Public API has fields "step" and "notify_by" combined into one step "type"
    # Step.NOTIFY is handled using NotificationChannelPublicAPIOptions class, but Step.WAIT is handled differently.
    TYPE_WAIT = "wait"

    class Meta:
        model = UserNotificationPolicy
        fields = ["id", "user_id", "position", "type", "duration", "manual_order", "important"]

    def create(self, validated_data):
        if "type" not in validated_data:
            raise exceptions.ValidationError({"type": "Type is required"})

        validated_data = self.correct_validated_data(validated_data)
        # type is alias for combined step + notify_by field in serializer
        # correct_validated_data parse type to step + notify_by
        # that is why step key is used instead of type below
        if "wait_delay" in validated_data and validated_data["step"] != UserNotificationPolicy.Step.WAIT:
            raise exceptions.ValidationError({"duration": "Duration can't be set"})

        # Remove "manual_order" and "order" fields from validated_data, so they are not passed to create method.
        # Policies are always created at the end of the list, and then moved to the desired position by _adjust_order.
        manual_order = validated_data.pop("manual_order")
        order = validated_data.pop("order", None)

        instance = UserNotificationPolicy.objects.create(**validated_data)

        if order is not None:
            self._adjust_order(instance, manual_order, order, created=True)

        return instance

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

    @staticmethod
    def _adjust_order(instance, manual_order, order, created):
        # Passing order=-1 means that the policy should be moved to the end of the list.
        if order == -1:
            if created:
                # The policy was just created, so it is already at the end of the list.
                return

            order = instance.max_order()
            # max_order() can't be None here because at least one instance exists – the one we are moving.
            assert order is not None

        # Negative order is not allowed.
        if order < 0:
            raise BadRequest(detail="Invalid value for position field")

        # manual_order=True is intended for use by Terraform provider only, and is not a documented feature.
        # Orders are swapped instead of moved when using Terraform, because Terraform may issue concurrent requests
        # to create / update / delete multiple policies. "Move to" operation is not deterministic in this case, and
        # final order of policies may be different depending on the order in which requests are processed. On the other
        # hand, the result of concurrent "swap" operations is deterministic and does not depend on the order in
        # which requests are processed.
        if manual_order:
            instance.swap(order)
        else:
            instance.to(order)


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

        # Remove "manual_order" and "order" fields from validated_data, so they are not passed to update method.
        manual_order = validated_data.pop("manual_order")
        order = validated_data.pop("order", None)
        if order is not None:
            self._adjust_order(instance, manual_order, order, created=False)

        return super().update(instance, validated_data)
