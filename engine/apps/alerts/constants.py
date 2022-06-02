class ActionSource:
    (
        SLACK,
        WEB,
        TWILIO,
        TELEGRAM,
    ) = range(4)


TASK_DELAY_SECONDS = 1

NEXT_ESCALATION_DELAY = 5
