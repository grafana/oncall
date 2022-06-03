class TwilioMessageStatuses(object):
    """
    https://www.twilio.com/docs/sms/tutorials/how-to-confirm-delivery-python?code-sample=code-handle-a-sms-statuscallback&code-language=Python&code-sdk-version=5.x#receive-status-events-in-your-web-application
    https://www.twilio.com/docs/sms/api/message-resource#message-status-values
    """

    ACCEPTED = 10
    QUEUED = 20
    SENDING = 30
    SENT = 40
    FAILED = 50
    DELIVERED = 60
    UNDELIVERED = 70
    RECEIVING = 80
    RECEIVED = 90
    READ = 100

    CHOICES = (
        (ACCEPTED, "accepted"),
        (QUEUED, "queued"),
        (SENDING, "sending"),
        (SENT, "sent"),
        (FAILED, "failed"),
        (DELIVERED, "delivered"),
        (UNDELIVERED, "undelivered"),
        (RECEIVING, "receiving"),
        (RECEIVED, "received"),
        (READ, "read"),
    )

    DETERMINANT = {
        "accepted": ACCEPTED,
        "queued": QUEUED,
        "sending": SENDING,
        "sent": SENT,
        "failed": FAILED,
        "delivered": DELIVERED,
        "undelivered": UNDELIVERED,
        "receiving": RECEIVING,
        "received": RECEIVED,
        "read": READ,
    }


class TwilioCallStatuses(object):
    """
    https://www.twilio.com/docs/voice/twiml#callstatus-values
    """

    QUEUED = 10
    RINGING = 20
    IN_PROGRESS = 30
    COMPLETED = 40
    BUSY = 50
    FAILED = 60
    NO_ANSWER = 70
    CANCELED = 80

    CHOICES = (
        (QUEUED, "queued"),
        (RINGING, "ringing"),
        (IN_PROGRESS, "in-progress"),
        (COMPLETED, "completed"),
        (BUSY, "busy"),
        (FAILED, "failed"),
        (NO_ANSWER, "no-answer"),
        (CANCELED, "canceled"),
    )

    DETERMINANT = {
        "queued": QUEUED,
        "ringing": RINGING,
        "in-progress": IN_PROGRESS,
        "completed": COMPLETED,
        "busy": BUSY,
        "failed": FAILED,
        "no-answer": NO_ANSWER,
        "canceled": CANCELED,
    }


class TwilioLogRecordType(object):
    VERIFICATION_START = 10
    VERIFICATION_CHECK = 20

    CHOICES = ((VERIFICATION_START, "verification start"), (VERIFICATION_CHECK, "verification check"))


class TwilioLogRecordStatus(object):
    # For verification and check it has used the same statuses
    # https://www.twilio.com/docs/verify/api/verification#verification-response-properties
    # https://www.twilio.com/docs/verify/api/verification-check

    PENDING = 10
    APPROVED = 20
    DENIED = 30
    # Our customized status for TwilioException
    ERROR = 40

    CHOICES = ((PENDING, "pending"), (APPROVED, "approved"), (DENIED, "denied"), (ERROR, "error"))

    DETERMINANT = {"pending": PENDING, "approved": APPROVED, "denied": DENIED, "error": ERROR}


TEST_CALL_TEXT = (
    "You are invited to check an incident from Grafana OnCall. "
    "Alert via {channel_name} with title {alert_group_name} triggered {alerts_count} times"
)
