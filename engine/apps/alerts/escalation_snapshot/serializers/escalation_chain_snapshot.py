from rest_framework import serializers

from apps.alerts.models.escalation_chain import EscalationChain


class EscalationChainSnapshotSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = EscalationChain
        fields = [
            "id",
            "name",
        ]
