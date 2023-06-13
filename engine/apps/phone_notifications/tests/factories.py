import factory

from apps.phone_notifications.models import PhoneCallRecord, SMSRecord


class PhoneCallRecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = PhoneCallRecord


class SMSRecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = SMSRecord
