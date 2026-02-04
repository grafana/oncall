import logging
import typing

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup
from apps.zoom.events.event_handler import ZoomEventHandler
from apps.zoom.events.types import EventAction

logger = logging.getLogger(__name__)


class AlertGroupActionHandler(ZoomEventHandler):
    """
    Handles alert group actions from Zoom interactive message buttons.
    """

    def is_match(self) -> bool:
        """Check if the event is an alert group action."""
        action = self._get_action()
        return action and action in [
            EventAction.ACKNOWLEDGE,
            EventAction.UNACKNOWLEDGE,
            EventAction.RESOLVE,
            EventAction.UNRESOLVE,
        ]

    def process(self) -> None:
        """Process the alert group action."""
        alert_group = self._get_alert_group()
        action = self._get_action()

        if not alert_group or not action:
            logger.warning("Could not process Zoom event: missing alert_group or action")
            return

        action_fn, fn_kwargs = self._get_action_function(alert_group, action)
        action_fn(user=self.user, action_source=ActionSource.ZOOM, **fn_kwargs)

    def _get_action(self) -> typing.Optional[EventAction]:
        """Extract the action from the event."""
        action_item = self.event.get("actionItem", {})
        value = action_item.get("value", "")
        
        if not value:
            return None

        try:
            parts = value.split("|")
            if len(parts) != 3:
                return None
            action_str = parts[0]
            return EventAction(action_str)
        except ValueError:
            logger.info(f"Zoom event action not found: {value}")
            return None

    def _get_alert_group(self) -> typing.Optional[AlertGroup]:
        """Extract the alert group from the event."""
        action_item = self.event.get("actionItem", {})
        value = action_item.get("value", "")
        
        if not value:
            return None

        try:
            parts = value.split("|")
            if len(parts) != 3:
                return None
            alert_pk = parts[1]
            return AlertGroup.objects.get(public_primary_key=alert_pk)
        except (ValueError, AlertGroup.DoesNotExist):
            return None

    def _get_action_function(
        self, alert_group: AlertGroup, action: EventAction
    ) -> typing.Tuple[typing.Callable, dict]:
        """Get the appropriate action function for the alert group."""
        action_to_fn = {
            EventAction.ACKNOWLEDGE: {
                "fn_name": "acknowledge_by_user_or_backsync",
                "kwargs": {},
            },
            EventAction.UNACKNOWLEDGE: {
                "fn_name": "un_acknowledge_by_user_or_backsync",
                "kwargs": {},
            },
            EventAction.RESOLVE: {
                "fn_name": "resolve_by_user_or_backsync",
                "kwargs": {},
            },
            EventAction.UNRESOLVE: {
                "fn_name": "un_resolve_by_user_or_backsync",
                "kwargs": {},
            },
        }

        fn_info = action_to_fn[action]
        fn = getattr(alert_group, fn_info["fn_name"])

        return fn, fn_info["kwargs"]
