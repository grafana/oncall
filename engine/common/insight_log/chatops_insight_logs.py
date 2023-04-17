import enum
import json
import logging

from .insight_logs_enabled_check import is_insight_logs_enabled

insight_logger = logging.getLogger("insight_logger")
logger = logging.getLogger(__name__)


class ChatOpsEvent(enum.Enum):
    WORKSPACE_CONNECTED = "workspace_connected"
    WORKSPACE_DISCONNECTED = "workspace_disconnected"
    CHANNEL_CONNECTED = "channel_connected"
    CHANNEL_DISCONNECTED = "channel_disconnected"
    USER_LINKED = "user_linked"
    USER_UNLINKED = "used_unlinked"
    DEFAULT_CHANNEL_CHANGED = "default_channel_changed"


class ChatOpsTypePlug(enum.Enum):
    # ChatOpsTypePlug provides backend_id string for chatops integration not supporting messaging_backends.
    SLACK = "slack"
    TELEGRAM = "telegram"


def write_chatops_insight_log(author, event_name: ChatOpsEvent, chatops_type: str, **kwargs):
    try:
        organization = author.organization

        if is_insight_logs_enabled(organization):
            tenant_id = organization.stack_id
            user_id = author.public_primary_key
            username = json.dumps(author.username)

            log_line = f"tenant_id={tenant_id} author_id={user_id} author={username} action_type=chat_ops action_name={event_name.value} chat_ops_type={chatops_type.lower()}"  # noqa
            for k, v in kwargs.items():
                log_line += f" {k}={json.dumps(v)}"

            insight_logger.info(log_line)
    except Exception as e:
        logger.warning(f"insight_log.failed_to_write_chatops_insight_log exception={e}")
