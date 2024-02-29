import typing

from django.db import models

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertReceiveChannel


class ConnectionData(typing.TypedDict):
    id: str
    backsync: bool


class AlertReceiveChannelConnection(models.Model):
    source_channel = models.ForeignKey(
        "AlertReceiveChannel", on_delete=models.CASCADE, related_name="connected_alert_receive_channels"
    )
    connected_channel = models.ForeignKey(
        "AlertReceiveChannel", on_delete=models.CASCADE, related_name="source_alert_receive_channels"
    )
    backsync = models.BooleanField(default=False)

    class Meta:
        unique_together = ("source_channel", "connected_channel")

    @staticmethod
    def connect_channels(
        source_channel: "AlertReceiveChannel",
        connections_data: typing.List[ConnectionData],
    ) -> None:
        connections_data = {data["id"]: data["backsync"] for data in connections_data}
        channels_to_connect = source_channel.organization.alert_receive_channels.filter(
            public_primary_key__in=connections_data.keys()
        ).exclude(id=source_channel.id)
        connections_to_create = []
        for channel in channels_to_connect:
            connections_to_create.append(
                AlertReceiveChannelConnection(
                    source_channel=source_channel,
                    connected_channel=channel,
                    backsync=connections_data[channel.public_primary_key],
                )
            )
        AlertReceiveChannelConnection.objects.bulk_create(connections_to_create, ignore_conflicts=True, batch_size=5000)

    @staticmethod
    def disconnect_channels(source_channel: "AlertReceiveChannel", disconnect_channels_ids: typing.List[str]) -> None:
        source_channel.connected_alert_receive_channels.filter(
            connected_channel_id__public_primary_key__in=disconnect_channels_ids
        ).delete()
