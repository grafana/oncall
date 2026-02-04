import logging
import typing

from apps.user_management.models import User

if typing.TYPE_CHECKING:
    from apps.zoom.events.types import ZoomInteractiveMessageAction

logger = logging.getLogger(__name__)


class ZoomEventHandler:
    """Base class for Zoom event handlers."""

    def __init__(self, user: User, event: "ZoomInteractiveMessageAction"):
        self.user = user
        self.event = event

    def is_match(self) -> bool:
        """Check if this handler should process the event."""
        raise NotImplementedError

    def process(self) -> None:
        """Process the event."""
        raise NotImplementedError
