from abc import ABC, abstractmethod


class UserAbstractRepresentative(ABC):
    HANDLER_PREFIX = "on_"

    @abstractmethod
    def is_applicable(self):
        return None

    @staticmethod
    def get_handlers_map():
        from apps.base.models import UserNotificationPolicyLogRecord

        return UserNotificationPolicyLogRecord.TYPE_TO_HANDLERS_MAP
