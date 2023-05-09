from django.db import models

from apps.phone_notifications.models import SMSRecord


class ProviderSMS(models.Model):
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
