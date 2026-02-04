import enum
import typing


class ZoomAlertGroupContext(typing.TypedDict):
    """Context for Zoom alert group actions."""
    action: str
    token: str
    alert: str


class ZoomBotNotificationPayload(typing.TypedDict):
    """Payload for Zoom bot notification events."""
    accountId: str
    channelName: str
    robotJid: str
    toJid: str
    userId: str
    userJid: str
    userName: str


class ZoomInteractiveMessageAction(typing.TypedDict):
    """Payload for interactive message actions from Zoom."""
    actionItem: dict
    messageId: str
    robotJid: str
    toJid: str
    userId: str
    accountId: str
    channelName: str
    timestamp: int


class EventAction(enum.StrEnum):
    """Actions that can be performed on alert groups."""
    ACKNOWLEDGE = "acknowledge"
    UNACKNOWLEDGE = "unacknowledge"
    RESOLVE = "resolve"
    UNRESOLVE = "unresolve"


class ZoomEventType(enum.StrEnum):
    """Types of Zoom webhook events."""
    BOT_NOTIFICATION = "bot_notification"
    INTERACTIVE_MESSAGE_ACTIONS = "interactive_message_actions"
    INTERACTIVE_MESSAGE_SELECT = "interactive_message_select"
    INTERACTIVE_MESSAGE_EDITABLE = "interactive_message_editable"
    BOT_INSTALLED = "bot_installed"
    BOT_UNINSTALLED = "bot_uninstalled"
