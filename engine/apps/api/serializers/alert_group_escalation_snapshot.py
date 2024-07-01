from rest_framework import serializers

from apps.api.serializers.escalation_policy import EscalationPolicySerializer
from apps.api.serializers.schedule_base import ScheduleFastSerializer
from apps.api.serializers.user import FastUserSerializer
from apps.api.serializers.user_group import UserGroupSerializer
from apps.api.serializers.webhook import WebhookFastSerializer


class EscalationPolicySnapshotAPISerializer(EscalationPolicySerializer):
    """Serializes AlertGroup escalation policies snapshots for API endpoint"""

    notify_to_users_queue = FastUserSerializer(many=True, read_only=True)
    notify_schedule = ScheduleFastSerializer(read_only=True)
    notify_to_group = UserGroupSerializer(read_only=True)
    custom_webhook = WebhookFastSerializer(read_only=True)

    class Meta(EscalationPolicySerializer.Meta):
        fields = [
            "step",
            "wait_delay",
            "notify_to_users_queue",
            "from_time",
            "to_time",
            "num_alerts_in_window",
            "num_minutes_in_window",
            "slack_integration_required",
            "custom_webhook",
            "notify_schedule",
            "notify_to_group",
            "important",
        ]
        read_only_fields = fields


class AlertGroupEscalationSnapshotAPISerializer(serializers.Serializer):
    """Serializes AlertGroup escalation snapshot for API endpoint"""

    escalation_chain = serializers.SerializerMethodField()
    channel_filter = serializers.SerializerMethodField()
    escalation_policies = EscalationPolicySnapshotAPISerializer(
        source="escalation_policies_snapshots", many=True, read_only=True
    )

    class Meta:
        fields = ["escalation_chain", "channel_filter", "escalation_policies"]

    def get_escalation_chain(self, obj):
        return {"name": obj.escalation_chain_snapshot.name}

    def get_channel_filter(self, obj):
        return {"name": obj.channel_filter_snapshot.str_for_clients}
