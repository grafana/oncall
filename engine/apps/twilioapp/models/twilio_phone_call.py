import logging

from django.db import models

from apps.phone_notifications.models import PhoneCallRecord
from apps.phone_notifications.phone_provider import ProviderPhoneCall

logger = logging.getLogger(__name__)


class TwilioCallStatuses:
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


class TwilioPhoneCall(ProviderPhoneCall, models.Model):
    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=TwilioCallStatuses.CHOICES,
    )

    phone_call_record = models.OneToOneField(
        "phone_notifications.PhoneCallRecord",
        on_delete=models.CASCADE,
        related_name="twilio_phone_call",
        null=False,
    )

    sid = models.CharField(
        blank=True,
        max_length=50,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def link_and_save(self, phone_call_record: PhoneCallRecord):
        self.phone_call_record = phone_call_record
        self.save()
