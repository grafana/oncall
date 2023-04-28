from rest_framework import serializers

from apps.alerts.models.custom_button import CustomButton
from apps.alerts.models.escalation_policy import EscalationPolicy
from apps.schedules.models import OnCallSchedule
from apps.user_management.models import User
from apps.webhooks.models import Webhook


class PrimaryKeyRelatedFieldWithNoneValue(serializers.PrimaryKeyRelatedField):
    """
    Returns None instead of ValidationError if related object does not exist
    """

    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().filter(pk=data).first()
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)


class ManyRelatedFieldWithNoneCleanup(serializers.ManyRelatedField):
    """
    Removes None values from ManyRelatedFields.
    Expected to be used with PrimaryKeyRelatedFieldWithNoneValue.

    Example:
    # We have input data with non-existent primary key

    PrimaryKeyRelatedField(many=True, queryset=...)  # raise ValidationError
    PrimaryKeyRelatedFieldWithNoneValue(many=True,  queryset=...) # will return [None] for non-existent id
    ManyRelatedFieldWithNoneCleanup(child_relation=PrimaryKeyRelatedField(queryset=...)) # raise ValidationError
    ManyRelatedFieldWithNoneCleanup(child_relation=PrimaryKeyRelatedFieldWithNoneValue(queryset=...)) # just return []
    """

    def to_internal_value(self, data):
        if isinstance(data, str) or not hasattr(data, "__iter__"):
            self.fail("not_a_list", input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail("empty")

        internal_value = []
        for item in data:
            child_internal_value = self.child_relation.to_internal_value(item)
            if child_internal_value is not None:
                internal_value.append(child_internal_value)
        return internal_value


class EscalationPolicySnapshotSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField()
    wait_delay = serializers.DurationField(allow_null=True)
    notify_to_users_queue = ManyRelatedFieldWithNoneCleanup(
        child_relation=PrimaryKeyRelatedFieldWithNoneValue(allow_null=True, queryset=User.objects)
    )
    escalation_counter = serializers.IntegerField(default=0)
    passed_last_time = serializers.DateTimeField(allow_null=True, default=None)
    custom_button_trigger = PrimaryKeyRelatedFieldWithNoneValue(allow_null=True, queryset=CustomButton.objects)
    custom_webhook = PrimaryKeyRelatedFieldWithNoneValue(allow_null=True, queryset=Webhook.objects, default=None)
    notify_schedule = PrimaryKeyRelatedFieldWithNoneValue(allow_null=True, queryset=OnCallSchedule.objects)
    num_alerts_in_window = serializers.IntegerField(allow_null=True, default=None)
    num_minutes_in_window = serializers.IntegerField(allow_null=True, default=None)
    pause_escalation = serializers.BooleanField(default=False)

    class Meta:
        model = EscalationPolicy
        fields = [
            "id",
            "order",
            "step",
            "wait_delay",
            "notify_to_users_queue",
            "last_notified_user",
            "from_time",
            "to_time",
            "num_alerts_in_window",
            "num_minutes_in_window",
            "custom_button_trigger",
            "custom_webhook",
            "notify_schedule",
            "notify_to_group",
            "escalation_counter",
            "passed_last_time",
            "pause_escalation",
        ]
