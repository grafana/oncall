from django.db import models


# Duplicate to avoid circular import to provide values for status field
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


class SMSRecord(models.Model):
    class Meta:
        db_table = "twilioapp_smsmessage"

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey(
        "alerts.Alert", on_delete=models.SET_NULL, null=True, default=None
    )  # deprecated
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)
    grafana_cloud_notification = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # deprecated. It's here for backward compatibility for sms sent during or shortly before migration.
    # Should be removed soon after migration
    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=TwilioSMSstatuses.CHOICES,
    )

    sid = models.CharField(
        blank=True,
        max_length=50,
    )


class ProviderSMS(models.Model):
    """
    ProviderSMS is an interface between SMSRecord and call data returned from PhoneProvider.
    Concrete provider sms be inherited from ProviderSMS.

    The idea is same as for ProviderCall - to save provider specific data without exposing them to PhoneBackend.
    """

    class Meta:
        abstract = True

    sms_record = models.OneToOneField(
        "phone_notifications.SMSRecord",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
        null=False,
    )

    def link_and_save(self, sms_record: SMSRecord):
        self.sms_record = sms_record
        self.save()
