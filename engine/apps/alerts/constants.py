import typing
from enum import Enum

from django.db.models import IntegerChoices


class ActionSource(IntegerChoices):
    SLACK = 0, "Slack"
    WEB = 1, "Web"
    PHONE = 2, "Phone"
    TELEGRAM = 3, "Telegram"
    API = 4, "API"


TASK_DELAY_SECONDS = 1

NEXT_ESCALATION_DELAY = 5


# AlertGroup states verbal
class AlertGroupState(str, Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"


# ServiceNow Integration
class ServiceNowStateMapping(typing.TypedDict):
    firing: typing.Optional[typing.Tuple[int, str]]
    acknowledged: typing.Optional[typing.Tuple[int, str]]
    resolved: typing.Optional[typing.Tuple[int, str]]
    silenced: typing.Optional[typing.Tuple[int, str]]


class ServiceNowSettings(typing.TypedDict):
    instance_url: str
    username: str
    password: str
    state_mapping: ServiceNowStateMapping
    is_configured: bool


ServiceNowEmptyMapping = {
    "firing": None,
    "acknowledged": None,
    "resolved": None,
    "silenced": None,
}
