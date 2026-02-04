import logging
import typing

from rest_framework.request import Request

from apps.zoom.events.event_handler import ZoomEventHandler
from apps.zoom.events.types import ZoomEventType, ZoomInteractiveMessageAction
from apps.user_management.models import User

logger = logging.getLogger(__name__)


class EventManager:
    """
    Manager for Zoom events.
    """

    @classmethod
    def process_interactive_action(cls, request: Request) -> None:
        """Process interactive message action from Zoom."""
        user = request.user
        event = request.data
        handler = cls.select_event_handler(user=user, event=event)
        
        if handler is None:
            logger.info("No event handler found for Zoom interactive action")
            return

        logger.info(f"Processing Zoom interactive action with handler: {handler.__class__.__name__}")
        handler.process()

    @classmethod
    def process_webhook(cls, request: Request) -> None:
        """
        Process incoming Zoom webhook events.
        
        Reference: https://developers.zoom.us/docs/api/rest/webhook-reference/
        """
        event_type = request.data.get("event", "")
        payload = request.data.get("payload", {})
        
        logger.info(f"Processing Zoom webhook: {event_type}")

        if event_type == ZoomEventType.INTERACTIVE_MESSAGE_ACTIONS:
            # Handle interactive message button clicks
            cls._handle_interactive_message_action(payload)
        elif event_type == ZoomEventType.BOT_NOTIFICATION:
            # Handle bot notifications (e.g., user messages to bot)
            cls._handle_bot_notification(payload)
        elif event_type == ZoomEventType.BOT_INSTALLED:
            cls._handle_bot_installed(payload)
        elif event_type == ZoomEventType.BOT_UNINSTALLED:
            cls._handle_bot_uninstalled(payload)
        else:
            logger.info(f"Unhandled Zoom webhook event: {event_type}")

    @staticmethod
    def select_event_handler(
        user: User, event: ZoomInteractiveMessageAction
    ) -> typing.Optional[ZoomEventHandler]:
        """Select the appropriate event handler for the event."""
        # Import here to avoid circular imports
        from apps.zoom.events.alert_group_actions_handler import AlertGroupActionHandler

        handler_classes = [AlertGroupActionHandler]
        
        for handler_class in handler_classes:
            handler = handler_class(user=user, event=event)
            if handler.is_match():
                return handler
        
        return None

    @classmethod
    def _handle_interactive_message_action(cls, payload: dict) -> None:
        """
        Handle interactive message action from webhook.
        
        Payload example:
        {
            "accountId": "xxx",
            "actionItem": {"text": "Acknowledge", "value": "ack_ALERT_PK"},
            "channelName": "devops-channel",
            "messageId": "xxx",
            "userId": "xxx",
            "userJid": "xxx@xmpp.zoom.us",
            "userName": "John Doe",
            "toJid": "xxx@conference.xmpp.zoom.us",
            ...
        }
        """
        logger.info(f"Interactive message action received: {payload}")
        
        # Extract user info from payload
        user_id = payload.get("userId", "")
        user_jid = payload.get("userJid", "")
        user_name = payload.get("userName", "")
        channel_jid = payload.get("toJid", "")
        message_id = payload.get("messageId", "")
        action_item = payload.get("actionItem", {})
        action_value = action_item.get("value", "")
        
        if not action_value:
            logger.warning("No action value in Zoom interactive message")
            return
        
        # Parse action value (format: "action_alertPK" or "silence_seconds_alertPK")
        action, alert_pk, silence_delay = cls._parse_action_value(action_value)
        
        if not action or not alert_pk:
            logger.warning(f"Invalid action value format: {action_value}")
            return
        
        logger.info(f"Processing action={action} for alert_pk={alert_pk} by user={user_name}, silence_delay={silence_delay}")
        
        # Get the user from Zoom user mapping
        user = cls._get_user_from_zoom(user_id, user_jid)
        
        # Process the action
        cls._execute_alert_action(
            action=action,
            alert_pk=alert_pk,
            user=user,
            user_name=user_name,
            user_jid=user_jid,
            channel_jid=channel_jid,
            message_id=message_id,
            silence_delay=silence_delay,
        )
    
    @staticmethod
    def _parse_action_value(value: str) -> typing.Tuple[str, str, typing.Optional[int]]:
        """
        Parse action value from button click.
        
        Supports formats:
        - "action_alertPK" (e.g., "ack_ABC123", "resolve_XYZ789")
        - "silence_seconds_alertPK" (e.g., "silence_3600_ABC123" for 1 hour)
        - "action|alertPK|token" (legacy format)
        
        Returns: (action, alert_pk, silence_delay or None)
        """
        silence_delay = None
        
        if "|" in value:
            parts = value.split("|")
            if len(parts) >= 2:
                return parts[0], parts[1], None
        elif "_" in value:
            parts = value.split("_")
            # Check for silence with delay: silence_seconds_alertPK
            if len(parts) == 3 and parts[0] == "silence":
                try:
                    silence_delay = int(parts[1])
                    return parts[0], parts[2], silence_delay
                except ValueError:
                    pass
            # Standard format: action_alertPK
            if len(parts) == 2:
                return parts[0], parts[1], None
        
        return "", "", None
    
    @staticmethod
    def _get_user_from_zoom(user_id: str, user_jid: str) -> typing.Optional[User]:
        """Get OnCall user from Zoom user ID."""
        from apps.zoom.models import ZoomUser
        
        try:
            zoom_user = ZoomUser.objects.get(zoom_user_id=user_id)
            return zoom_user.user
        except ZoomUser.DoesNotExist:
            logger.warning(f"Zoom user {user_id} not linked to OnCall user")
            return None
    
    @classmethod
    def _execute_alert_action(
        cls,
        action: str,
        alert_pk: str,
        user: typing.Optional[User],
        user_name: str,
        user_jid: str,
        channel_jid: str,
        message_id: str,
        silence_delay: typing.Optional[int] = None,
    ) -> None:
        """Execute the alert action and update the Zoom message."""
        from apps.alerts.constants import ActionSource
        from apps.alerts.models import AlertGroup
        from apps.zoom.client import ZoomClient
        from apps.zoom.alert_rendering import ZoomMessageRenderer
        
        # Get alert group
        try:
            alert_group = AlertGroup.objects.get(public_primary_key=alert_pk)
        except AlertGroup.DoesNotExist:
            logger.error(f"AlertGroup with pk={alert_pk} not found")
            return
        
        # Map action string to method
        action_map = {
            "ack": "acknowledge_by_user_or_backsync",
            "acknowledge": "acknowledge_by_user_or_backsync",
            "unack": "un_acknowledge_by_user_or_backsync",
            "unacknowledge": "un_acknowledge_by_user_or_backsync",
            "resolve": "resolve_by_user_or_backsync",
            "unresolve": "un_resolve_by_user_or_backsync",
            "silence": "silence_by_user_or_backsync",
            "unsilence": "un_silence_by_user_or_backsync",
        }
        
        method_name = action_map.get(action.lower())
        
        if not method_name:
            logger.info(f"Unknown action: {action}")
            # For unknown actions like "note", just log
            return
        
        if not user:
            logger.warning(f"Cannot execute action {action}: user not linked. Action by: {user_name}")
            # TODO: Could send an error message back to Zoom
            return
        
        # Execute the action
        try:
            method = getattr(alert_group, method_name)
            if action.lower() == "silence" and silence_delay is not None:
                method(user=user, action_source=ActionSource.ZOOM, silence_delay=silence_delay)
                logger.info(f"Executed {action} (delay={silence_delay}s) on alert_group {alert_pk} by {user.username}")
            else:
                method(user=user, action_source=ActionSource.ZOOM)
                logger.info(f"Executed {action} on alert_group {alert_pk} by {user.username}")
        except Exception as e:
            logger.error(f"Error executing {action}: {e}")
            return
        
        # Refresh alert_group to get updated state
        alert_group.refresh_from_db()
        
        # Update the Zoom message
        try:
            client = ZoomClient()
            renderer = ZoomMessageRenderer(alert_group)
            # Pass zoom user info to use @ mention in status text
            message_content = renderer.render_alert_group_message(
                action_user_name=user_name,
                action_user_jid=user_jid,
            )
            
            # Use the full body structure
            client.update_message_with_body(
                message_id=message_id,
                channel_id=channel_jid,
                user_jid=user_jid,
                header_text=message_content.get("header", "OnCall Alert"),
                sub_header_text=message_content.get("sub_header"),
                body=message_content.get("body", []),
            )
            logger.info(f"Updated Zoom message {message_id}")
        except Exception as e:
            logger.error(f"Error updating Zoom message: {e}", exc_info=True)

    @classmethod
    def _handle_bot_notification(cls, payload: dict) -> None:
        """Handle bot notification event."""
        logger.info(f"Bot notification received: {payload}")
        # Could be used for slash commands or direct messages to the bot

    @classmethod
    def _handle_bot_installed(cls, payload: dict) -> None:
        """Handle bot installed event."""
        logger.info(f"Bot installed: {payload}")
        # Could trigger setup workflows

    @classmethod
    def _handle_bot_uninstalled(cls, payload: dict) -> None:
        """Handle bot uninstalled event."""
        logger.info(f"Bot uninstalled: {payload}")
        # Could trigger cleanup workflows
