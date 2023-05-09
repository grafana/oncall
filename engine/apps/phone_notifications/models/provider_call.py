from django.db import models

from apps.phone_notifications.models import PhoneCallRecord


class ProviderPhoneCall(models.Model):
    """
    ProviderPhoneCall is an interface between PhoneCallRecord and call data returned from PhoneProvider.

    Some phone providers allows to track status of call or gather pressed digits (we use it to ack/resolve alert group).
    It is needed to link phone call and alert group without exposing internals of concrete phone provider to PhoneBackend.
    """

    class Meta:
        abstract = True

    phone_call_record = models.OneToOneField(
        "phone_notifications.PhoneCallRecord",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        related_query_name="%(app_label)s_%(class)ss",
        null=False,
    )

    def link_and_save(self, phone_call_record: PhoneCallRecord):
        self.phone_call_record = phone_call_record
        self.save()
