from abc import ABC, abstractmethod

from django.apps import apps


class UserAbstractRepresentative(ABC):
    HANDLER_PREFIX = "on_"

    @abstractmethod
    def is_applicable(self):
        return None

    @staticmethod
    def get_handlers_map():
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
        return UserNotificationPolicyLogRecord.TYPE_TO_HANDLERS_MAP
