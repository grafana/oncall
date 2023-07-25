import logging
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup
from apps.api.permissions import RBACPermission, user_is_authorized
from apps.telegram.models import TelegramToUserConnector
from apps.telegram.renderers.keyboard import CODE_TO_ACTION_MAP, Action
from apps.telegram.updates.update_handlers import UpdateHandler
from apps.telegram.utils import CallbackQueryFactory
from apps.user_management.models import User

logger = logging.getLogger(__name__)

PERMISSION_DENIED = """You don't have a permission to perform this action!
Consider connecting your Telegram account on user settings page ⚙"""


@dataclass
class ActionContext:
    alert_group: AlertGroup
    action: Action
    action_data: str


class ButtonPressHandler(UpdateHandler):
    def matches(self) -> bool:
        is_callback_query = self.update.callback_query is not None
        return is_callback_query

    def process_update(self) -> None:
        data = self.update.callback_query.data
        action_context = self._get_action_context(data)

        fn, fn_kwargs = self._map_action_context_to_fn(action_context)
        user = self._get_user(action_context)

        has_permission = self._check_permission(user=user, alert_group=action_context.alert_group)

        if has_permission:
            fn(user=user, action_source=ActionSource.TELEGRAM, **fn_kwargs)
            logger.info(f"User {user} triggered '{fn.__name__}'")
        else:
            self.update.callback_query.answer(PERMISSION_DENIED, show_alert=True)
            logger.info(f"User {user} has no permission to trigger '{fn.__name__}'")

    def _get_user(self, action_context: ActionContext) -> Optional[User]:
        connector = TelegramToUserConnector.objects.filter(
            telegram_chat_id=self.update.effective_user.id,
            user__organization=action_context.alert_group.channel.organization,
        ).last()
        return connector.user if connector is not None else None

    @staticmethod
    def _check_permission(user: Optional[User], alert_group: AlertGroup) -> bool:
        if not user:
            return False

        has_permission = user_is_authorized(user, [RBACPermission.Permissions.CHATOPS_WRITE])
        return user.organization == alert_group.channel.organization and has_permission

    @classmethod
    def _get_action_context(cls, data: str) -> ActionContext:
        args = CallbackQueryFactory.decode_data(data)

        alert_group_pk = args[0]
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)

        action_value = args[1]
        try:
            # if action encoded as action_code - cast it to the action_string
            action_value = int(action_value)
            action_name = CODE_TO_ACTION_MAP[action_value]
        except ValueError:
            # support legacy messages with action_name in callback data
            action_name = action_value
        action = Action(action_name)

        action_data = args[2] if len(args) >= 3 and not cls._is_oncall_identifier(args[2]) else None

        return ActionContext(alert_group=alert_group, action=action, action_data=action_data)

    @staticmethod
    def _is_oncall_identifier(string: str) -> bool:
        # determines if piece of data passed via callback_data is oncall_identifier
        # x-oncall-org-id is kept here for backward compatibility.
        return string.startswith("x-oncall-org-id") or string.startswith("oncall-uuid")

    @staticmethod
    def _map_action_context_to_fn(action_context: ActionContext) -> Tuple[Callable, dict]:
        action_to_fn = {
            Action.RESOLVE: "resolve_by_user",
            Action.UNRESOLVE: "un_resolve_by_user",
            Action.ACKNOWLEDGE: "acknowledge_by_user",
            Action.UNACKNOWLEDGE: "un_acknowledge_by_user",
            Action.SILENCE: {
                "fn_name": "silence_by_user",
                "kwargs": {"silence_delay": int(action_context.action_data) if action_context.action_data else None},
            },
            Action.UNSILENCE: "un_silence_by_user",
        }

        fn_info = action_to_fn[action_context.action]
        fn_name = fn_info["fn_name"] if isinstance(fn_info, dict) else fn_info
        fn_kwargs = fn_info["kwargs"] if isinstance(fn_info, dict) else {}

        fn = getattr(action_context.alert_group, fn_name)

        return fn, fn_kwargs
