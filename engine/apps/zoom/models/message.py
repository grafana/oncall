from django.db import models

from apps.alerts.models import AlertGroup


class ZoomMessage(models.Model):
    """Model to track messages sent to Zoom Team Chat."""

    (
        ALERT_GROUP_MESSAGE,
        LOG_MESSAGE,
    ) = range(2)

    ZOOM_MESSAGE_CHOICES = (
        (ALERT_GROUP_MESSAGE, "Alert group message"),
        (LOG_MESSAGE, "Log message"),
    )

    message_id = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=100)
    message_type = models.IntegerField(choices=ZOOM_MESSAGE_CHOICES)

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="zoom_messages",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["alert_group", "message_type", "channel_id"],
                name="unique_zoom_alert_group_message_type_channel_id",
            )
        ]

        indexes = [
            models.Index(fields=["channel_id", "message_id"]),
        ]

    def __str__(self):
        return f"ZoomMessage({self.message_id})"

    @staticmethod
    def create_message(alert_group: AlertGroup, message_id: str, channel_id: str, message_type: int):
        """Create a new ZoomMessage record."""
        return ZoomMessage.objects.create(
            alert_group=alert_group,
            message_id=message_id,
            channel_id=channel_id,
            message_type=message_type,
        )
