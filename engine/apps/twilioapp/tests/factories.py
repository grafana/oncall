import factory

from apps.twilioapp.models import PhoneCall, SMSMessage


class PhoneCallFactory(factory.DjangoModelFactory):
    class Meta:
        model = PhoneCall


class SMSFactory(factory.DjangoModelFactory):
    class Meta:
        model = SMSMessage
