"""
[Documentation](https://api.slack.com/reference/interaction-payloads/shortcuts)
"""

import typing

from apps.slack.types.common import BaseEvent, PayloadType


class MessageActionPayload(BaseEvent):
    """
    [Documentation](https://api.slack.com/reference/interaction-payloads/shortcuts)
    """

    type: typing.Literal[PayloadType.MESSAGE_ACTION]
    """
    Helps identify which type of interactive component sent the payload.
    [Global shortcuts](https://api.slack.com/interactivity/shortcuts#global) will return `shortcut`,
    [message shortcuts](https://api.slack.com/interactivity/shortcuts#message) will return `message_action`.
    """
