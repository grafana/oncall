import typing

from .handlers import Handler, SlackInstallationHandler
from .types import Event


class ChatopsEventsHandler:
    """
    ChatopsEventsHandler is a root hander which receive incoming event from Chatops-Proxy and choose the right
    handler to process it.
    """

    HANDLERS: typing.List[typing.Type[Handler]] = [SlackInstallationHandler]

    def handle(self, event_data: Event):
        for h in self.HANDLERS:
            if h.match(event_data):
                h.handle(event_data.get("data", {}))
                break
