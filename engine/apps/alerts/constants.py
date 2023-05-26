from enum import Enum


class ActionSource:
    (
        SLACK,
        WEB,
        PHONE,
        TELEGRAM,
    ) = range(4)


TASK_DELAY_SECONDS = 1

NEXT_ESCALATION_DELAY = 5


# AlertGroup states verbal
class AlertGroupState(str, Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"
