from django.db import models
from twilio.rest import Client


class TwilioAccount(models.Model):
    name = models.CharField(max_length=100)
    account_sid = models.CharField(max_length=64, null=False, blank=False, unique=True)
    auth_token = models.CharField(max_length=64, null=True, default=None)
    api_key_sid = models.CharField(max_length=64, null=True, default=None)
    api_key_secret = models.CharField(max_length=64, null=True, default=None)

    def get_twilio_api_client(self):
        if self.api_key_sid and self.api_key_secret:
            return Client(self.api_key_sid, self.api_key_secret, self.account_sid)
        else:
            return Client(self.account_sid, self.auth_token)


class TwilioSender(models.Model):
    name = models.CharField(max_length=100, null=False, default="Default")
    # Note: country_code does not have + prefix here
    country_code = models.CharField(max_length=16, null=True, default=None)
    account = models.ForeignKey(
        "twilioapp.TwilioAccount", on_delete=models.CASCADE, related_name="%(app_label)s_%(class)s_account"
    )

    class Meta:
        abstract = True


class TwilioSmsSender(TwilioSender):
    # Sender for sms is phone number, short code or alphanumeric id
    sender = models.CharField(max_length=16, null=False, blank=False)


class TwilioPhoneCallSender(TwilioSender):
    number = models.CharField(max_length=16, null=False, blank=False)


class TwilioVerificationSender(TwilioSender):
    verify_service_sid = models.CharField(max_length=64, null=False, blank=False)
