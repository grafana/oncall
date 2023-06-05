from django.db import models


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


# Deprecated model. Kept here for backward compatibility, should be removed after phone notificator release
class TwilioLogRecord(models.Model):

    user = models.ForeignKey("user_management.User", on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=16)

    type = models.PositiveSmallIntegerField(
        choices=TwilioLogRecordType.CHOICES, default=TwilioLogRecordType.VERIFICATION_START
    )

    status = models.PositiveSmallIntegerField(
        choices=TwilioLogRecordStatus.CHOICES, default=TwilioLogRecordStatus.PENDING
    )

    payload = models.TextField(null=True, default=None)

    error_message = models.TextField(null=True, default=None)

    succeed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
