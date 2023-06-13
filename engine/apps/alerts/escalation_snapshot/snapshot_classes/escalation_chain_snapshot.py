from apps.alerts.escalation_snapshot.serializers import EscalationChainSnapshotSerializer


class EscalationChainSnapshot:
    __slots__ = ("id", "name")

    serializer = EscalationChainSnapshotSerializer

    def __init__(self, id, name):
        self.id = id
        self.name = name
