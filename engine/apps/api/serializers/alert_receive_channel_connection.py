from rest_framework import serializers

from apps.alerts.models import AlertReceiveChannel, AlertReceiveChannelConnection
from apps.api.serializers.alert_receive_channel import FastAlertReceiveChannelSerializer


class AlertReceiveChannelSourceChannelSerializer(serializers.ModelSerializer):
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="source_alert_receive_channel", read_only=True)
    backsync = serializers.BooleanField()

    class Meta:
        model = AlertReceiveChannelConnection
        fields = ["alert_receive_channel", "backsync"]


class AlertReceiveChannelConnectedChannelSerializer(serializers.ModelSerializer):
    alert_receive_channel = FastAlertReceiveChannelSerializer(source="connected_alert_receive_channel", read_only=True)
    backsync = serializers.BooleanField()

    class Meta:
        model = AlertReceiveChannelConnection
        fields = ["alert_receive_channel", "backsync"]


class AlertReceiveChannelConnectionSerializer(serializers.ModelSerializer):
    source_alert_receive_channels = AlertReceiveChannelSourceChannelSerializer(read_only=True, many=True)
    connected_alert_receive_channels = AlertReceiveChannelConnectedChannelSerializer(read_only=True, many=True)

    class Meta:
        model = AlertReceiveChannel
        fields = ["source_alert_receive_channels", "connected_alert_receive_channels"]


class AlertReceiveChannelNewConnectionSerializer(serializers.Serializer):
    id = serializers.CharField()
    backsync = serializers.BooleanField()
