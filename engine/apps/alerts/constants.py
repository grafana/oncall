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
