"""
[Documentation](https://api.slack.com/legacy/interactive-messages#receiving-action-invocations)
"""

import enum
import typing

from apps.slack.types.common import BaseEvent, Channel, PayloadType


class InteractiveMessageActionType(enum.StrEnum):
    SELECT = "select"
    BUTTON = "button"


class InteractiveMessageAction(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/legacy/interactive-messages#checking-action-type)
    """

    name: str
    type: InteractiveMessageActionType


class OriginalMessage(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/legacy/interactive-messages#checking-action-type)
    """

    text: str
    username: str
    bot_id: str
    attachments: typing.List
    type: typing.Literal["message"]
    subtype: str
    ts: str


class InteractiveMessagesPayload(BaseEvent):
    """
    [Documentation](https://api.slack.com/legacy/interactive-messages#receiving-action-invocations)
    """

    type: typing.Literal[PayloadType.INTERACTIVE_MESSAGE]
    """
    Helps identify which type of interactive component sent the payload.

    An interactive element in a block will have a type of `block_actions`, whereas an interactive element in a
    [message attachment](https://api.slack.com/reference/messaging/attachments) will have a type of
    `interactive_message`.
    """

    trigger_id: str
    """
    A short-lived ID that can be [used to open modals](https://api.slack.com/interactivity/handling#modal_responses).

    Triggers expire in three seconds. Use them before you lose them. You'll receive a `trigger_expired` error when
    using a method with an expired `trigger_id`.

    Triggers may only be used once. You may perform just one operation with a `trigger_id`. Subsequent attempts are presented with a `trigger_exchanged` error.

    For more info see [here](https://api.slack.com/interactivity/handling#modal_responses).
    """

    actions: typing.List[InteractiveMessageAction]

    token: str
    """
    Represents a deprecated verification token feature.

    You should validate the request payload, however, and the best way to do so is to
    [use the signing secret provided to your app](https://api.slack.com/reference/interaction-payloads/block-actions#:~:text=use%20the%20signing%20secret%20provided%20to%20your%20app).
    """  # noqa: E501

    channel: Channel

    original_message: OriginalMessage
