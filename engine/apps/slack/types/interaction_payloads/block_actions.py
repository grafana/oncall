"""
[Documentation](https://api.slack.com/reference/interaction-payloads/block-actions)
"""

import enum
import typing

from apps.slack.types.common import BaseEvent, Channel, Container, Message, PayloadType


class BlockActionType(enum.StrEnum):
    """
    https://api.slack.com/reference/interaction-payloads/block-actions#payload_timing
    """

    USERS_SELECT = "users_select"
    BUTTON = "button"
    STATIC_SELECT = "static_select"
    CONVERSATIONS_SELECT = "conversations_select"
    CHANNELS_SELECT = "channels_select"
    OVERFLOW = "overflow"
    DATEPICKER = "datepicker"
    CHECKBOXES = "checkboxes"


class BlockAction(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/reference/interaction-payloads/block-actions)
    """

    block_id: str
    """
    Identifies the block within a surface that contained the interactive component that was used.

    See the [reference guide for the block you're using](https://api.slack.com/reference/block-kit/blocks)
    for more info on the `block_id` field.
    """

    action_id: str
    """
    Identifies the interactive component itself.

    Some blocks can contain multiple interactive components, so the `block_id` alone may not be specific enough to
    identify the source component.See the
    [reference guide for the interactive element you're using](https://api.slack.com/reference/block-kit/block-elements)
    for more info on the `action_id` field.
    """

    value: str
    """
    Set by your app when you composed the blocks, this is the value that was specified in the interactive component
    when an interaction happened.

    For example, a select menu will have multiple possible values depending on what the
    user picks from the menu, and `value` will identify the chosen option. See the
    [reference guide for the interactive element you're using](https://api.slack.com/reference/block-kit/block-elements)
    for more info on the `value` field.
    """


class BlockActionsPayload(BaseEvent):
    """
    [Documentation](https://api.slack.com/reference/interaction-payloads/block-actions)
    """

    type: typing.Literal[PayloadType.BLOCK_ACTIONS]
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

    container: Container
    """
    The container where this block action took place.
    """

    actions: typing.Optional[typing.List[BlockAction]]
    """
    (Optional) Contains data from the specific
    [interactive component](https://api.slack.com/reference/block-kit/interactive-components) that was used.

    [App surfaces](https://api.slack.com/surfaces) can contain
    [blocks](https://api.slack.com/reference/block-kit/blocks) with multiple interactive components, and each of those
    components can have multiple values selected by users.
    """

    token: str
    """
    Represents a deprecated verification token feature.

    You should validate the request payload, however, and the best way to do so is to
    [use the signing secret provided to your app](https://api.slack.com/reference/interaction-payloads/block-actions#:~:text=use%20the%20signing%20secret%20provided%20to%20your%20app).
    """  # noqa: E501

    channel: typing.Optional[Channel]
    """
    (Optional) The channel where this block action took place.
    """

    message: typing.Optional[Message]
    """
    (Optional) The message where this block action took place, if the block was contained in a message.
    """
