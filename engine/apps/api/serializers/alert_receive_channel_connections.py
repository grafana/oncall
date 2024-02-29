from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel, AlertReceiveChannelConnection
from apps.api.serializers.alert_receive_channel import FastAlertReceiveChannelSerializer


class AlertReceiveChannelConnectedChannelsBaseSerializer(serializers.ModelSerializer):
    backsync = serializers.BooleanField()

    class Meta:
        model = AlertReceiveChannelConnection
        fields = ["alert_receive_channel", "backsync"]


class AlertReceiveChannelSourceChannelSerializer(AlertReceiveChannelConnectedChannelsBaseSerializer):
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="source_channel", read_only=True)


class AlertReceiveChannelConnectedChannelSerializer(AlertReceiveChannelConnectedChannelsBaseSerializer):
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="connected_channel", read_only=True)


class AlertReceiveChannelConnectionSerializer(serializers.ModelSerializer):
    source_alert_receive_channels = AlertReceiveChannelSourceChannelSerializer(read_only=True, many=True)
    connected_alert_receive_channels = AlertReceiveChannelConnectedChannelSerializer(read_only=True, many=True)

    class Meta:
        model = AlertReceiveChannel
        fields = ["source_alert_receive_channels", "connected_alert_receive_channels"]


class AlertReceiveChannelNewConnectionSerializer(serializers.Serializer):
    id = serializers.CharField()
    backsync = serializers.BooleanField()

    class Meta:
        fields = ["id", "backsync"]
