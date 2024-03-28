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


class AlertGroupExternalID(models.Model):
    """
    This model represents an external ID for an alert group. This is used to keep track of the alert group in
    the external system (e.g. ServiceNow).
    """

    source_alert_receive_channel = models.ForeignKey(
        "AlertReceiveChannel", on_delete=models.CASCADE, related_name="external_ids"
    )
    alert_group = models.ForeignKey("AlertGroup", on_delete=models.CASCADE, related_name="external_ids")
    value = models.CharField(max_length=512)

    class Meta:
        unique_together = ("source_alert_receive_channel", "alert_group")
        indexes = [
            models.Index(fields=["value"]),
        ]
