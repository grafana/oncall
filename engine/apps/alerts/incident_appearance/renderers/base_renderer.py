import typing
from abc import ABC, abstractmethod

from django.db.models import QuerySet
from django.utils.functional import cached_property

if typing.TYPE_CHECKING:
    from apps.alerts.models import Alert, AlertGroup, BundledNotification


class AlertBaseRenderer(ABC):
    def __init__(self, alert: "Alert"):
        self.alert = alert

    @cached_property
    def templated_alert(self):
        return self.templater_class(self.alert).render()

    @property
    @abstractmethod
    def templater_class(self):
        raise NotImplementedError


class AlertGroupBaseRenderer(ABC):
    def __init__(self, alert_group: "AlertGroup", alert: typing.Optional["Alert"] = None):
        if alert is None:
            alert = alert_group.alerts.first()

        self.alert_group = alert_group
        self.alert_renderer = self.alert_renderer_class(alert)

    @property
    @abstractmethod
    def alert_renderer_class(self):
        raise NotImplementedError


class AlertGroupBundleBaseRenderer:
    MAX_ALERT_GROUPS_TO_RENDER = 3
    MAX_CHANNELS_TO_RENDER = 1

    def __init__(self, notifications: "QuerySet[BundledNotification]"):
        self.notifications = notifications
