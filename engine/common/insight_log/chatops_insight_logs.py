import enum
import logging

insight_logger = logging.getLogger("insight_logger")


class ChatOpsEvent(enum.Enum):
    WORKSPACE_CONNECTED = "started"
    WORKSPACE_DISCONNECTED = "finished"
    CHANNEL_CONNECTED = "channel_connected"
    CHANNEL_DISCONNECTED = "channel_disconnected"
    USER_LINKED = "user_linked"
    USER_UNLINKED = "used_unlinked"
    DEFAULT_CHANNEL_CHANGED = "default_channel_changed"


class ChatOpsType(enum.Enum):
    # Keep in sync with messaging backends' id.
    # In perfect world backend_ids should be used intead of this enums
    # It can be achieved when we move refactor slack and telegram to use the messaging_backend system.
    SLACK = "SLACK"
    MSTEAMS = "MSTEAMS"
    TELEGRAM = "TELEGRAM"


def chatops_insight_log(organization, author, event_name: ChatOpsEvent, chatops_type: ChatOpsType, **kwargs):
    tenant_id = organization.stack_id
    user_id = author.public_primary_key
    username = author.username

    log_line = f"tenant_id={tenant_id} author_id={user_id} author={username} event_type=chat_ops event_name={event_name} chat_ops_type={chatops_type}"  # noqa
    for k, v in kwargs.items():
        log_line += f" {k}={v}"

    insight_logger.info(log_line)
