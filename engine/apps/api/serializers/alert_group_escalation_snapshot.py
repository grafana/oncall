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

    class EscalationChainSnapshotAPISerializer(serializers.Serializer):
        name = serializers.CharField()

    class ChannelFilterSnapshotAPISerializer(serializers.Serializer):
        name = serializers.CharField(source="str_for_clients")

    escalation_chain = EscalationChainSnapshotAPISerializer(read_only=True, source="escalation_chain_snapshot")
    channel_filter = ChannelFilterSnapshotAPISerializer(read_only=True, source="channel_filter_snapshot")
    escalation_policies = EscalationPolicySnapshotAPISerializer(
        source="escalation_policies_snapshots", many=True, read_only=True
    )

    class Meta:
        fields = ["escalation_chain", "channel_filter", "escalation_policies"]
