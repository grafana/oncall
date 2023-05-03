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
STATE_FIRING = "firing"
STATE_ACKNOWLEDGED = "acknowledged"
STATE_RESOLVED = "resolved"
STATE_SILENCED = "silenced"

ALERTGROUP_STATES = [STATE_FIRING, STATE_ACKNOWLEDGED, STATE_RESOLVED, STATE_SILENCED]
