import logging
import typing

from rest_framework.request import Request

from apps.mattermost.events.event_handler import MattermostEventHandler
from apps.mattermost.events.types import MattermostEvent
from apps.user_management.models import User

logger = logging.getLogger(__name__)


class EventManager:
    """
    Manager for mattermost events
    """

    @classmethod
    def process_request(cls, request: Request):
        user = request.user
        event = request.data
        handler = cls.select_event_handler(user=user, event=event)
        if handler is None:
            logger.info("No event handler found")
            return

        logger.info(f"Processing mattermost event with handler: {handler.__class__.__name__}")
        handler.process()

    @staticmethod
    def select_event_handler(user: User, event: MattermostEvent) -> typing.Optional[MattermostEventHandler]:
        handler_classes = MattermostEventHandler.__subclasses__()
        for handler_class in handler_classes:
            handler = handler_class(user=user, event=event)
            if handler.is_match():
                return handler
        return None
