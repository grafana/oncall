import typing
from abc import ABC, abstractmethod

from django.utils.functional import cached_property

if typing.TYPE_CHECKING:
    from apps.alerts.models import Alert, AlertGroup


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
