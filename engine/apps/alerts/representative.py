import logging
from abc import ABC, abstractmethod

from django.apps import apps

logger = logging.getLogger(__name__)


class AlertGroupAbstractRepresentative(ABC):
    HANDLER_PREFIX = "on_"

    @abstractmethod
    def is_applicable(self):
        return None

    @staticmethod
    def get_handlers_map():
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        return AlertGroupLogRecord.ACTIONS_TO_HANDLERS_MAP

    @classmethod
    def on_create_alert(cls, **kwargs):
        raise NotImplementedError
