import factory

from apps.twilioapp.models.twilio_sender import (
    TwilioAccount,
    TwilioPhoneCallSender,
    TwilioSmsSender,
    TwilioVerificationSender,
)


class TwilioAccountFactory(factory.DjangoModelFactory):
    class Meta:
        model = TwilioAccount


class TwilioPhoneCallSenderFactory(factory.DjangoModelFactory):
    class Meta:
        model = TwilioPhoneCallSender


class TwilioSmsSenderFactory(factory.DjangoModelFactory):
    class Meta:
        model = TwilioSmsSender


class TwilioVerificationSenderFactory(factory.DjangoModelFactory):
    class Meta:
        model = TwilioVerificationSender
