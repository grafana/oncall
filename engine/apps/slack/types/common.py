import enum
import typing

from .block_elements import BlockElement
from .composition_objects import PlainText


class PayloadType(enum.StrEnum):
    INTERACTIVE_MESSAGE = "interactive_message"
    SLASH_COMMAND = "slash_command"
    EVENT_CALLBACK = "event_callback"
    BLOCK_ACTIONS = "block_actions"
    DIALOG_SUBMISSION = "dialog_submission"
    VIEW_SUBMISSION = "view_submission"
    MESSAGE_ACTION = "message_action"


class EventType(enum.StrEnum):
    """
    [Documentation](https://api.slack.com/events)
    """

    MESSAGE = "message"
    """
    A message was sent to a channel

    [Documentation](https://api.slack.com/events/message)
    """

    MESSAGE_CHANNEL = "channel"
    """
    NOTE: this event doesn't actually seem to exist? This is here for legacy reasons and should
    probably be re-investgated and/or deleted?
    """

    USER_CHANGE = "user_change"
    """
    NOTE: This is deprecated in favour of `user_profile_changed`. Kept for legacy reasons.

    A member's data has changed

    [Documentation](https://api.slack.com/events/user_change)
    """

    USER_PROFILE_CHANGED = "user_profile_changed"
    """
    A user's profile data has changed

    [Documentation](https://api.slack.com/events/user_profile_changed)
    """

    APP_MENTION = "app_mention"
    """
    Subscribe to only the message events that mention your app or bot

    [Documentation](https://api.slack.com/events/app_mention)
    """

    MEMBER_JOINED_CHANNEL = "member_joined_channel"
    """
    A user joined a public channel, private channel or MPDM.

    [Documentation](https://api.slack.com/events/member_joined_channel)
    """

    IM_OPEN = "im_open"
    """
    You opened a DM

    [Documentation](https://api.slack.com/events/im_open)
    """

    APP_HOME_OPENED = "app_home_opened"
    """
    User clicked into your App Home

    [Documentation](https://api.slack.com/events/app_home_opened)
    """

    SUBTEAM_CREATED = "subteam_created"
    """
    A User Group has been added to the workspace

    [Documentation](https://api.slack.com/events/subteam_created)
    """

    SUBTEAM_UPDATED = "subteam_updated"
    """
    An existing User Group has been updated or its members changed

    [Documentation](https://api.slack.com/events/subteam_updated)
    """

    SUBTEAM_MEMBERS_CHANGED = "subteam_members_changed"
    """
    The membership of an existing User Group has changed

    [Documentation](https://api.slack.com/events/subteam_members_changed)
    """

    CHANNEL_DELETED = "channel_deleted"
    """
    A channel was deleted

    [Documentation](https://api.slack.com/events/channel_deleted)
    """

    CHANNEL_CREATED = "channel_created"
    """
    A channel was created

    [Documentation](https://api.slack.com/events/channel_created)
    """

    CHANNEL_RENAMED = "channel_rename"
    """
    A channel was renamed

    [Documentation](https://api.slack.com/events/channel_rename)
    """

    CHANNEL_ARCHIVED = "channel_archive"
    """
    A channel was archived

    [Documentation](https://api.slack.com/events/channel_archive)
    """

    CHANNEL_UNARCHIVED = "channel_unarchive"
    """
    A channel was unarchived

    [Documentation](https://api.slack.com/events/channel_unarchive)
    """


class MessageEventSubtype(enum.StrEnum):
    """
    [Documentation](https://api.slack.com/events/message#subtypes)
    """

    MESSAGE_CHANGED = "message_changed"
    """
    A message was changed

    [Documentation](https://api.slack.com/events/message/message_changed)
    """

    MESSAGE_DELETED = "message_deleted"
    """
    A message was deleted

    [Documentation](https://api.slack.com/events/message/message_deleted)
    """

    BOT_MESSAGE = "bot_message"
    """
    A message was posted by an integration

    [Documentation](https://api.slack.com/events/message/bot_message)
    """


class Style(enum.StrEnum):
    DEFAULT = "default"
    PRIMARY = "primary"
    DANGER = "danger"


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


class Container(typing.TypedDict):
    type: str


class Message(typing.TypedDict):
    type: typing.Literal["message"]
    bot_id: str
    text: str
    user: str
    ts: str


class ModalView(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/surfaces/modals#view-object-fields)
    """

    type: typing.Literal["modal"]
    """
    Required. The type of view. Set to `modal` for modals.
    """

    title: PlainText
    """
    Required. The title that appears in the top-left of the modal.

    Must be a [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) with a max
    length of 24 characters.
    """

    blocks: typing.List[BlockElement]
    """
    Required. An array of [blocks](https://api.slack.com/reference/block-kit/blocks) that defines the content of the
    view.

    Max of 100 blocks.
    """

    close: PlainText
    """
    An optional [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) that
    defines the text displayed in the close button at the bottom-right of the view.

    Max length of 24 characters.
    """

    submit: PlainText
    """
    An optional [plain_text text element](https://api.slack.com/reference/block-kit/composition-objects#text) that
    defines the text displayed in the submit button at the bottom-right of the view.

    `submit` is required when an input block is within the blocks array.

    Max length of 24 characters.
    """

    private_metadata: str
    """
    An optional string that will be sent to your app in `view_submission` and `block_actions` events.

    Max length of 3000 characters.
    """

    callback_id: str
    """
    An identifier to recognize interactions and submissions of this particular view. Don't use this to store sensitive
    information (use `private_metadata` instead).

    Max length of 255 characters.
    """

    clear_on_close: bool
    """
    When set to `true`, clicking on the `close` button will clear all views in a modal and close it.

    Defaults to `false`.
    """

    notify_on_close: bool
    """
    Indicates whether Slack will send your request URL a `view_closed` event when a user clicks the `close` button.

    Defaults to `false`.
    """

    external_id: str
    """
    A custom identifier that must be unique for all views on a per-team basis.
    """

    submit_disabled: bool
    """
    When set to `true`, disables the `submit` button until the user has completed one or more inputs.

    This property is for [configuration modals](https://api.slack.com/reference/workflows/configuration-view).
    """


class Channel(typing.TypedDict):
    id: str
    name: str


class BaseEvent(typing.TypedDict):
    type: PayloadType

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
