from abc import ABC, abstractmethod

from telegram import Update


class UpdateHandler(ABC):
    """
    Update handler for Telegram update
    After making new handler by subclassing this abstract class, make sure to add it to __init__.py
    """

    def __init__(self, update: Update):
        self.update = update

    @abstractmethod
    def matches(self) -> bool:
        pass

    @abstractmethod
    def process_update(self) -> None:
        pass
