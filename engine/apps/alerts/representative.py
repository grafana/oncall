import logging
from abc import ABC, abstractmethod

1


class AlertGroupAbstractRepresentative(ABC):
    HANDLER_PREFIX = "on_"

    @abstractmethod
    def is_applicable(self):
        return None

    @staticmethod
    def get_handlers_map():
        from apps.alerts.models import AlertGroupLogRecord

        return AlertGroupLogRecord.ACTIONS_TO_HANDLERS_MAP

    @classmethod
    def on_create_alert(cls, **kwargs):
        raise NotImplementedError
