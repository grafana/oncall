from abc import ABC, abstractmethod

from apps.mattermost.events.types import MattermostEvent
from apps.user_management.models import User


class MattermostEventHandler(ABC):
    def __init__(self, event: MattermostEvent, user: User):
        self.event: MattermostEvent = event
        self.user: User = user

    @abstractmethod
    def is_match(self) -> bool:
        pass

    @abstractmethod
    def process(self) -> None:
        pass
