class ActionSource:
    (
        SLACK,
        WEB,
        TWILIO,
        TELEGRAM,
    ) = range(4)


TASK_DELAY_SECONDS = 1

NEXT_ESCALATION_DELAY = 5

# AlertGroup states verbal
STATE_NEW = "new"
STATE_ACKNOWLEDGED = "acknowledged"
STATE_RESOLVED = "resolved"
STATE_SILENCED = "silenced"

ALERTGROUP_STATES = [STATE_NEW, STATE_ACKNOWLEDGED, STATE_RESOLVED, STATE_SILENCED]
