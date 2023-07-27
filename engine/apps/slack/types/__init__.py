from .block_action import BlockActionEvent
from .common import BlockActionType, PayloadType  # noqa: F401
from .view_submission import ViewSubmissionEvent

EventPayload = BlockActionEvent | ViewSubmissionEvent
