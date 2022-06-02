from django.db import models

from apps.twilioapp.constants import TwilioLogRecordStatus, TwilioLogRecordType


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
