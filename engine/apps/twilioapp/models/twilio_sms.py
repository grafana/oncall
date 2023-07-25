from django.db import models

from apps.phone_notifications.models import ProviderSMS


class TwilioSMSstatuses:
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


class TwilioSMS(ProviderSMS, models.Model):
    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=TwilioSMSstatuses.CHOICES,
    )

    # https://www.twilio.com/docs/sms/api/message-resource#message-properties
    sid = models.CharField(
        blank=True,
        max_length=50,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
