import logging
import typing

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup
from apps.mattermost.events.event_handler import MattermostEventHandler
from apps.mattermost.events.types import EventAction
from apps.mattermost.models import MattermostMessage

logger = logging.getLogger(__name__)


class AlertGroupActionHandler(MattermostEventHandler):
    """
    Handles the alert group actions from the mattermost message buttons
    """

    def is_match(self):
        action = self._get_action()
        return action and action in [
            EventAction.ACKNOWLEDGE,
            EventAction.UNACKNOWLEDGE,
            EventAction.RESOLVE,
            EventAction.UNRESOLVE,
        ]

    def process(self):
        alert_group = self._get_alert_group()
        action = self._get_action()

        if not alert_group or not action:
            return

        action_fn, fn_kwargs = self._get_action_function(alert_group, action)
        action_fn(user=self.user, action_source=ActionSource.MATTERMOST, **fn_kwargs)

    def _get_action(self) -> typing.Optional[EventAction]:
        if "context" not in self.event or "action" not in self.event["context"]:
            return

        try:
            action = self.event["context"]["action"]
            return EventAction(action)
        except ValueError:
            logger.info(f"Mattermost event action not found {action}")
            return

    def _get_alert_group(self) -> typing.Optional[AlertGroup]:
        return self._get_alert_group_from_event() or self._get_alert_group_from_message()

    def _get_alert_group_from_event(self) -> typing.Optional[AlertGroup]:
        if "context" not in self.event or "alert" not in self.event["context"]:
            return

        try:
            alert_group = AlertGroup.objects.get(pk=self.event["context"]["alert"])
        except AlertGroup.DoesNotExist:
            return

        return alert_group

    def _get_alert_group_from_message(self) -> typing.Optional[AlertGroup]:
        try:
            mattermost_message = MattermostMessage.objects.get(
                channel_id=self.event["channel_id"], post_id=self.event["post_id"]
            )
            return mattermost_message.alert_group
        except MattermostMessage.DoesNotExist:
            logger.info(
                f"Mattermost message not found for channel_id: {self.event['channel_id']} and post_id {self.event['post_id']}"
            )
            return

    def _get_action_function(self, alert_group: AlertGroup, action: EventAction) -> typing.Tuple[typing.Callable, dict]:
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
            EventAction.UNRESOLVE: {"fn_name": "un_resolve_by_user_or_backsync", "kwargs": {}},
        }

        fn_info = action_to_fn[action]
        fn = getattr(alert_group, fn_info["fn_name"])

        return fn, fn_info["kwargs"]
