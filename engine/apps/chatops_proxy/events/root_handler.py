import logging
import typing

from .handlers import Handler, SlackInstallHandler, SlackUninstallHandler
from .types import Event

logger = logging.getLogger(__name__)


class ChatopsEventsHandler:
    """
    ChatopsEventsHandler is a root handler which receives event from Chatops-Proxy and chooses the handler to process it.
    """

    HANDLERS: typing.List[typing.Type[Handler]] = [SlackInstallHandler, SlackUninstallHandler]

    def handle(self, event_data: Event) -> bool:
        """
        handle iterates over all handlers and chooses the first one that matches the event.
        Returns True if a handler was found and False otherwise.
        """
        logger.info(f"msg=\"ChatopsEventsHandler: Handling\" event_type={event_data.get('event_type')}")
        for h in self.HANDLERS:
            if h.match(event_data):
                logger.info(
                    f"msg=\"ChatopsEventsHandler: Found matching handler {h.__name__}\" event_type={event_data.get('event_type')}"
                )
                self._exec(h.handle, event_data.get("data", {}))
                return True
        logger.error(f"msg=\"ChatopsEventsHandler: No handler found\" event_type={event_data.get('event_type')}")
        return False

    def _exec(self, handlefunc: typing.Callable[[dict], None], data: dict):
        """
        _exec is a helper method to execute a handler's handle method.
        """
        return handlefunc(data)
