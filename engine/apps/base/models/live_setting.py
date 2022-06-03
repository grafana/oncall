from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField

from apps.base.utils import LiveSettingValidator
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_live_setting():
    prefix = "L"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while LiveSetting.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="LiveSetting"
        )
        failure_counter += 1

    return new_public_primary_key


class LiveSetting(models.Model):
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_live_setting,
    )
    name = models.CharField(max_length=50, unique=True)
    value = JSONField(null=True, default=None)
    error = models.TextField(null=True, default=None)

    AVAILABLE_NAMES = (
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_NUMBER",
        "TWILIO_VERIFY_SERVICE_SID",
        "TELEGRAM_TOKEN",
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
        "SLACK_SIGNING_SECRET",
        "SEND_ANONYMOUS_USAGE_STATS",
        "GRAFANA_CLOUD_ONCALL_TOKEN",
        "GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED",
        "GRAFANA_CLOUD_NOTIFICATIONS_ENABLED",
    )

    DESCRIPTIONS = {
        "SLACK_SIGNING_SECRET": (
            "Check <a href='"
            "https://github.com/grafana/amixr/blob/main/DEVELOPER.md#slack-application-setup"
            "'>this instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update Slack credentials."
        ),
        "SLACK_CLIENT_OAUTH_SECRET": (
            "Check <a href='"
            "https://github.com/grafana/amixr/blob/main/DEVELOPER.md#slack-application-setup"
            "'>this instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update Slack credentials."
        ),
        "SLACK_CLIENT_OAUTH_ID": (
            "Check <a href='"
            "https://github.com/grafana/amixr/blob/main/DEVELOPER.md#slack-application-setup"
            "'>this instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update Slack credentials."
        ),
        "TWILIO_ACCOUNT_SID": (
            "Twilio username to allow amixr send sms and make phone calls, "
            "<a href='https://support.twilio.com/hc/en-us/articles/223136027-Auth-Tokens-and-How-to-Change-Them'>"
            "more info</a>."
        ),
        "TWILIO_AUTH_TOKEN": (
            "Twilio password to allow amixr send sms and make calls, "
            "<a href='https://support.twilio.com/hc/en-us/articles/223136027-Auth-Tokens-and-How-to-Change-Them'>"
            "more info</a>."
        ),
        "TWILIO_NUMBER": (
            "Number from which you will receive calls and SMS, "
            "<a href='https://www.twilio.com/docs/phone-numbers'>more info</a>."
        ),
        "TWILIO_VERIFY_SERVICE_SID": (
            "SID of Twilio service for number verification. "
            "You can create a service in Twilio web interface. "
            "twilio.com -> verify -> create new service."
        ),
        "SENDGRID_API_KEY": (
            "Sendgrid api key to send emails, "
            "<a href='https://sendgrid.com/docs/ui/account-and-settings/api-keys/'>more info</a>."
        ),
        "SENDGRID_FROM_EMAIL": (
            "Address to send emails, <a href='https://sendgrid.com/docs/ui/sending-email/senders/'>" "more info</a>."
        ),
        "SENDGRID_SECRET_KEY": "It is the secret key to secure receiving inbound emails.",
        "SENDGRID_INBOUND_EMAIL_DOMAIN": "Domain to receive emails for inbound emails integration.",
        "TELEGRAM_TOKEN": (
            "Secret token for Telegram bot, you can get one via " "<a href='https://t.me/BotFather'>BotFather</a>."
        ),
        "SEND_ANONYMOUS_USAGE_STATS": (
            "Grafana OnCall will send anonymous, but uniquely-identifiable usage analytics to Grafana Labs."
            " These statistics are sent to https://stats.grafana.org/.  For more information on what's sent, look at"
            "https://github.com/..."  # TODO: add url to usage stats code
        ),
        "GRAFANA_CLOUD_ONCALL_TOKEN": "Secret token for Grafana Cloud OnCall instance.",
        "GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED": "Enable hearbeat integration with Grafana Cloud OnCall.",
        "GRAFANA_CLOUD_NOTIFICATIONS_ENABLED": "Enable SMS/call notifications via Grafana Cloud OnCall",
    }

    SECRET_SETTING_NAMES = (
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_VERIFY_SERVICE_SID",
        "SENDGRID_API_KEY",
        "SENDGRID_SECRET_KEY",
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
        "SLACK_SIGNING_SECRET",
        "TELEGRAM_TOKEN",
        "GRAFANA_CLOUD_ONCALL_TOKEN",
    )

    def __str__(self):
        return self.name

    @property
    def description(self):
        return self.DESCRIPTIONS.get(self.name)

    @property
    def default_value(self):
        return self._get_setting_from_setting_file(self.name)

    @property
    def is_secret(self):
        return self.name in self.SECRET_SETTING_NAMES

    @classmethod
    def get_setting(cls, setting_name):
        if not settings.FEATURE_LIVE_SETTINGS_ENABLED:
            return cls._get_setting_from_setting_file(setting_name)

        if setting_name not in cls.AVAILABLE_NAMES:
            raise ValueError(
                f"Setting with name '{setting_name}' is not in list of available names {cls.AVAILABLE_NAMES}"
            )

        live_setting = cls.objects.filter(name=setting_name).first()
        if live_setting is not None:
            return live_setting.value
        else:
            return cls._get_setting_from_setting_file(setting_name)

    @classmethod
    def populate_settings_if_needed(cls):
        settings_in_db = cls.objects.filter(name__in=cls.AVAILABLE_NAMES).values_list("name", flat=True)
        setting_names_to_populate = set(cls.AVAILABLE_NAMES) - set(settings_in_db)

        for setting_name in setting_names_to_populate:
            cls.objects.create(name=setting_name, value=cls._get_setting_from_setting_file(setting_name))

    @staticmethod
    def _get_setting_from_setting_file(setting_name):
        return getattr(settings, setting_name)

    def save(self, *args, **kwargs):
        if self.name not in self.AVAILABLE_NAMES:
            raise ValueError(
                f"Setting with name '{self.name}' is not in list of available names {self.AVAILABLE_NAMES}"
            )

        self.error = LiveSettingValidator(live_setting=self).get_error()
        super().save(*args, **kwargs)
