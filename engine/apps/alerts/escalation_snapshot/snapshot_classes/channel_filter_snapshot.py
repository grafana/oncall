from apps.alerts.escalation_snapshot.serializers import ChannelFilterSnapshotSerializer


class ChannelFilterSnapshot:
    __slots__ = ("id", "str_for_clients", "notify_in_slack", "notify_in_telegram", "notification_backends")

    serializer = ChannelFilterSnapshotSerializer

    def __init__(self, id, str_for_clients, notify_in_slack, notify_in_telegram, notification_backends):
        self.id = id
        self.str_for_clients = str_for_clients
        self.notify_in_slack = notify_in_slack
        self.notify_in_telegram = notify_in_telegram
        self.notification_backends = notification_backends
