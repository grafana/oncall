from rest_framework import serializers

from apps.alerts.escalation_snapshot.serializers import (
    ChannelFilterSnapshotSerializer,
    EscalationChainSnapshotSerializer,
    EscalationPolicySnapshotSerializer,
)


class EscalationSnapshotSerializer(serializers.Serializer):
    channel_filter_snapshot = ChannelFilterSnapshotSerializer(allow_null=True, default=None)
    escalation_chain_snapshot = EscalationChainSnapshotSerializer(allow_null=True, default=None)
    last_active_escalation_policy_order = serializers.IntegerField(allow_null=True, default=None)
    escalation_policies_snapshots = EscalationPolicySnapshotSerializer(many=True, default=list)
    slack_channel_id = serializers.CharField(allow_null=True, default=None)
    pause_escalation = serializers.BooleanField(allow_null=True, default=False)
    next_step_eta = serializers.DateTimeField(allow_null=True, default=None)

    class Meta:
        fields = [
            "channel_filter_snapshot",
            "escalation_chain_snapshot",
            "last_active_escalation_policy_order",
            "escalation_policies_snapshots",
            "slack_channel_id",
            "pause_escalation",
            "next_step_eta",
        ]
