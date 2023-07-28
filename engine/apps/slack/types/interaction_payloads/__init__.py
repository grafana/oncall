from .block_actions import BlockActionsPayload
from .dialog_submission import DialogSubmissionPayload
from .interactive_messages import InteractiveMessagesPayload
from .shortcuts import MessageActionPayload
from .slash_command import SlashCommandPayload
from .view_submission import ViewSubmissionPayload


class EventPayload:
    BlockActionsPayload = BlockActionsPayload
    DialogSubmissionPayload = DialogSubmissionPayload
    InteractiveMessagesPayload = InteractiveMessagesPayload
    MessageActionPayload = MessageActionPayload
    SlashCommandPayload = SlashCommandPayload
    ViewSubmissionPayload = ViewSubmissionPayload

    Any = (
        BlockActionsPayload
        | DialogSubmissionPayload
        | InteractiveMessagesPayload
        | MessageActionPayload
        | SlashCommandPayload
        | ViewSubmissionPayload
    )
