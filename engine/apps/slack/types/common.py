import enum
import typing


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


class PayloadType(enum.StrEnum):
    INTERACTIVE_MESSAGE = "interactive_message"
    SLASH_COMMAND = "slash_command"
    EVENT_CALLBACK = "event_callback"
    BLOCK_ACTIONS = "block_actions"
    DIALOG_SUBMISSION = "dialog_submission"
    VIEW_SUBMISSION = "view_submission"
    MESSAGE_ACTION = "message_action"


class User(typing.TypedDict):
    id: str
    """user's `public_primary_key`"""

    username: str
    name: str
    team_id: str
    """team's `public_primary_key`"""


class Team(typing.TypedDict):
    id: str
    domain: str


class Text(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/reference/block-kit/composition-objects#text)

    An object containing some text, formatted either as `plain_text` or using `mrkdwn`.
    """

    type: typing.Literal["plain_text"] | typing.Literal["mrkdwn"]
    """
    The formatting to use for this text object. Can be one of `plain_text` or `mrkdwn`.
    """

    text: str
    """
    The text for the block. This field accepts any of the standard
    [text formatting markup](https://api.slack.com/reference/surfaces/formatting) when `type` is `mrkdwn`.
    The minimum length is 1 and maximum length is 3000 characters.
    """

    emoji: typing.Optional[bool]
    """
    Indicates whether emojis in a text field should be escaped into the colon emoji format.

    This field is only usable when `type` is `plain_text`.
    """

    verbatim: typing.Optional[bool]
    """
    When set to `false` (as is default) URLs will be auto-converted into links, conversation names will be link-ified,
    and certain mentions will be automatically parsed.

    Using a value of `true` will skip any preprocessing of this nature, although you can still include
    [manual parsing strings](https://api.slack.com/reference/surfaces/formatting#advanced). This field is only usable
    when `type` is `mrkdwn`.
    """


class Container(typing.TypedDict):
    type: str  # TODO: strongly type this as a string literal
    message_ts: str
    channel_id: str
    is_ephemeral: bool


class Message(typing.TypedDict):
    type: typing.Literal["message"]
    bot_id: str
    text: str
    user: str
    ts: str


class View(typing.TypedDict):
    pass


class Channel(typing.TypedDict):
    id: str
    name: str


class BaseEvent(typing.TypedDict):
    user: User
    """
    The user who interacted to trigger this request.
    """

    team: Team | None
    """
    The workspace the app is installed on. Null if the app is org-installed.
    """

    api_app_id: str
    """
    A string representing the app ID.
    """
