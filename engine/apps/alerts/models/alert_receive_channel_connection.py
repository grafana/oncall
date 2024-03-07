from django.db import models


class AlertReceiveChannelConnection(models.Model):
    """
    This model represents a connection between two integrations (e.g. when an Alertmanager integration is connected to a
    ServiceNow integration).
    """

    source_alert_receive_channel = models.ForeignKey(
        "AlertReceiveChannel", on_delete=models.CASCADE, related_name="connected_alert_receive_channels"
    )
    connected_alert_receive_channel = models.ForeignKey(
        "AlertReceiveChannel", on_delete=models.CASCADE, related_name="source_alert_receive_channels"
    )
    backsync = models.BooleanField(default=False)

    class Meta:
        ordering = ["source_alert_receive_channel", "connected_alert_receive_channel"]
        unique_together = ("source_alert_receive_channel", "connected_alert_receive_channel")
