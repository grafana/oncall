import logging

from rest_framework import status

from apps.alerts.models import AlertGroup
from apps.alerts.representative import AlertGroupAbstractRepresentative
from apps.zoom.alert_rendering import ZoomMessageRenderer
from apps.zoom.client import ZoomClient
from apps.zoom.exceptions import ZoomAPIException, ZoomAPITokenInvalid
from apps.zoom.tasks import on_alert_group_action_triggered_async, on_create_alert_async

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertGroupZoomRepresentative(AlertGroupAbstractRepresentative):
    """Representative for handling alert group actions in Zoom."""

    def __init__(self, log_record) -> None:
        self.log_record = log_record

    def is_applicable(self):
        """Check if this representative should handle the log record."""
        from apps.zoom.models import ZoomChannel

        organization = self.log_record.alert_group.channel.organization
        handler_exists = self.log_record.type in self.get_handler_map().keys()

        zoom_channels = ZoomChannel.objects.filter(organization=organization)
        return handler_exists and zoom_channels.exists()

    @staticmethod
    def get_handler_map():
        """Return mapping of log record types to handler names."""
        from apps.alerts.models import AlertGroupLogRecord

        return {
            AlertGroupLogRecord.TYPE_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_AUTO_UN_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_RESOLVED: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_RESOLVED: "alert_group_action",
            AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED: "alert_group_action",
            AlertGroupLogRecord.TYPE_SILENCE: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_SILENCE: "alert_group_action",
            AlertGroupLogRecord.TYPE_ATTACHED: "alert_group_action",
            AlertGroupLogRecord.TYPE_UNATTACHED: "alert_group_action",
        }

    def on_alert_group_action(self, alert_group: AlertGroup):
        """Update Zoom message when an alert group action is triggered."""
        from apps.zoom.models import ZoomMessage

        logger.info(f"Update Zoom message for alert_group {alert_group.pk}")
        
        zoom_message = alert_group.zoom_messages.filter(
            message_type=ZoomMessage.ALERT_GROUP_MESSAGE
        ).order_by("created_at").first()
        
        if not zoom_message:
            logger.warning(f"No Zoom message found for alert group {alert_group.pk}")
            return

        # Render the updated message (returns dict with header, sub_header, body)
        renderer = ZoomMessageRenderer(alert_group)
        message_content = renderer.render_alert_group_message()

        try:
            client = ZoomClient()
            client.update_message_with_body(
                message_id=zoom_message.message_id,
                channel_id=zoom_message.channel_id,
                header_text=message_content.get("header", "OnCall Alert"),
                sub_header_text=message_content.get("sub_header"),
                body=message_content.get("body", []),
            )
            logger.info(f"Successfully updated Zoom message {zoom_message.message_id}")
        except ZoomAPITokenInvalid:
            logger.error(f"Zoom API token is invalid. Could not update message for alert group {alert_group.pk}")
        except ZoomAPIException as ex:
            logger.error(f"Zoom API error: {ex}")
            if ex.status not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]:
                raise ex

    @staticmethod
    def on_create_alert(**kwargs):
        """Handle new alert creation."""
        alert_pk = kwargs["alert"]
        on_create_alert_async.apply_async((alert_pk,))

    @staticmethod
    def on_alert_group_action_triggered(**kwargs):
        """Handle alert group action trigger."""
        from apps.alerts.models import AlertGroupLogRecord

        log_record = kwargs["log_record"]
        if isinstance(log_record, AlertGroupLogRecord):
            log_record_id = log_record.pk
        else:
            log_record_id = log_record
        on_alert_group_action_triggered_async.apply_async((log_record_id,))

    def get_handler(self):
        """Get the appropriate handler for the log record type."""
        handler_name = self.get_handler_name()
        logger.info(f"Using '{handler_name}' handler to process alert action in Zoom")
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
        else:
            handler = None

        return handler

    def get_handler_name(self):
        """Get the handler method name for the log record type."""
        return self.HANDLER_PREFIX + self.get_handler_map()[self.log_record.type]
