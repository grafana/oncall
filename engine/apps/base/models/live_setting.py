from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField
from django.db.utils import IntegrityError

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
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_HOST_USER",
        "EMAIL_HOST_PASSWORD",
        "EMAIL_USE_TLS",
        "EMAIL_USE_SSL",
        "EMAIL_FROM_ADDRESS",
        "INBOUND_EMAIL_ESP",
        "INBOUND_EMAIL_DOMAIN",
        "INBOUND_EMAIL_WEBHOOK_SECRET",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY_SID",
        "TWILIO_API_KEY_SECRET",
        "TWILIO_NUMBER",
        "TWILIO_VERIFY_SERVICE_SID",
        "TELEGRAM_TOKEN",
        "TELEGRAM_WEBHOOK_HOST",
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
        "SLACK_SIGNING_SECRET",
        "SLACK_INSTALL_RETURN_REDIRECT_HOST",
        "SEND_ANONYMOUS_USAGE_STATS",
        "GRAFANA_CLOUD_ONCALL_TOKEN",
        "GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED",
        "GRAFANA_CLOUD_NOTIFICATIONS_ENABLED",
        "DANGEROUS_WEBHOOKS_ENABLED",
        "PHONE_PROVIDER",
        "ZVONOK_API_KEY",
        "ZVONOK_CAMPAIGN_ID",
        "ZVONOK_AUDIO_ID",
        "ZVONOK_SPEAKER_ID",
        "ZVONOK_POSTBACK_CALL_ID",
        "ZVONOK_POSTBACK_CAMPAIGN_ID",
        "ZVONOK_POSTBACK_STATUS",
        "ZVONOK_POSTBACK_USER_CHOICE",
        "ZVONOK_POSTBACK_USER_CHOICE_ACK",
        "ZVONOK_VERIFICATION_CAMPAIGN_ID",
        "EXOTEL_ACCOUNT_SID",
        "EXOTEL_API_KEY",
        "EXOTEL_API_TOKEN",
        "EXOTEL_APP_ID",
        "EXOTEL_CALLER_ID",
        "EXOTEL_SMS_SENDER_ID",
        "EXOTEL_SMS_VERIFICATION_TEMPLATE",
        "EXOTEL_SMS_DLT_ENTITY_ID",
    )

    DESCRIPTIONS = {
        "EMAIL_HOST": "SMTP server host. This email server will be used to notify users via email.",
        "EMAIL_PORT": "SMTP server port",
        "EMAIL_HOST_USER": "SMTP server user",
        "EMAIL_HOST_PASSWORD": "SMTP server password",
        "EMAIL_USE_TLS": "SMTP enable/disable TLS",
        "EMAIL_USE_SSL": "SMTP enable/disable SSL. Should be used mutually exclusively with EMAIL_USE_TLS.",
        "EMAIL_FROM_ADDRESS": "Email address used to send emails. If not specified, EMAIL_HOST_USER will be used.",
        "INBOUND_EMAIL_DOMAIN": "Inbound email domain",
        "INBOUND_EMAIL_ESP": (
            "Inbound email ESP name. "
            "Available options: amazon_ses, mailgun, mailjet, mandrill, postal, postmark, sendgrid, sparkpost"
        ),
        "INBOUND_EMAIL_WEBHOOK_SECRET": "Inbound email webhook secret",
        "SLACK_SIGNING_SECRET": (
            "Check <a href='"
            "https://grafana.com/docs/oncall/latest/open-source/#slack-setup"
            "' target='_blank'>instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update them."
        ),
        "SLACK_CLIENT_OAUTH_SECRET": (
            "Check <a href='"
            "https://grafana.com/docs/oncall/latest/open-source/#slack-setup"
            "' target='_blank'>instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update them."
        ),
        "SLACK_CLIENT_OAUTH_ID": (
            "Check <a href='"
            "https://grafana.com/docs/oncall/latest/open-source/#slack-setup"
            "' target='_blank'>instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update them."
        ),
        "SLACK_INSTALL_RETURN_REDIRECT_HOST": (
            "Check <a href='"
            "https://grafana.com/docs/oncall/latest/open-source/#slack-setup"
            "' target='_blank'>instruction</a> for details how to set up Slack. "
            "Slack secrets can't be verified on the backend, please try installing the Slack Bot "
            "after you update them."
        ),
        "TWILIO_ACCOUNT_SID": (
            "Twilio account SID/username to allow OnCall to send SMSes and make phone calls, see "
            "<a href='https://support.twilio.com/hc/en-us/articles/223136027-Auth-Tokens-and-How-to-Change-Them' target='_blank'>"
            "here</a> for more info. Required."
        ),
        "TWILIO_API_KEY_SID": (
            "Twilio API key SID/username to allow OnCall to send SMSes and make phone calls, see "
            "<a href='https://www.twilio.com/docs/iam/keys/api-key' target='_blank'>"
            "here</a> for more info. Either (TWILIO_API_KEY_SID + TWILIO_API_KEY_SECRET) or TWILIO_AUTH_TOKEN is required."
        ),
        "TWILIO_API_KEY_SECRET": (
            "Twilio API key secret/password to allow OnCall to send SMSes and make phone calls, see "
            "<a href='https://www.twilio.com/docs/iam/keys/api-key' target='_blank'>"
            "here</a> for more info. Either (TWILIO_API_KEY_SID + TWILIO_API_KEY_SECRET) or TWILIO_AUTH_TOKEN is required."
        ),
        "TWILIO_AUTH_TOKEN": (
            "Twilio password to allow OnCall to send SMSes and make calls, see "
            "<a href='https://support.twilio.com/hc/en-us/articles/223136027-Auth-Tokens-and-How-to-Change-Them' target='_blank'>"
            "here</a> for more info. Either (TWILIO_API_KEY_SID + TWILIO_API_KEY_SECRET) or TWILIO_AUTH_TOKEN is required."
        ),
        "TWILIO_NUMBER": (
            "Number from which you will receive calls and SMSes, "
            "<a href='https://www.twilio.com/docs/phone-numbers' target='_blank'>more info</a>."
        ),
        "TWILIO_VERIFY_SERVICE_SID": (
            "SID of Twilio service for number verification. "
            "You can create a service in Twilio web interface. "
            "twilio.com -> verify -> create new service."
        ),
        "TELEGRAM_TOKEN": (
            "Secret token for Telegram bot, you can get one via <a href='https://t.me/BotFather' target='_blank'>BotFather</a>."
        ),
        "TELEGRAM_WEBHOOK_HOST": (
            "Externally available URL for Telegram to make requests. Must use https and ports 80, 88, 443, 8443."
        ),
        "SEND_ANONYMOUS_USAGE_STATS": (
            "Grafana OnCall will send anonymous, but uniquely-identifiable usage analytics to Grafana Labs."
            " These statistics are sent to https://stats.grafana.org/.  For more information on what's sent, look at the "
            "<a href='https://github.com/grafana/oncall/blob/dev/engine/apps/oss_installation/usage_stats.py#L29' target='_blank'> source code</a>."
        ),
        "GRAFANA_CLOUD_ONCALL_TOKEN": "Secret token for Grafana Cloud OnCall instance.",
        "GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED": "Enable heartbeat integration with Grafana Cloud OnCall.",
        "GRAFANA_CLOUD_NOTIFICATIONS_ENABLED": "Enable SMS/call notifications via Grafana Cloud OnCall",
        "DANGEROUS_WEBHOOKS_ENABLED": "Enable outgoing webhooks to private networks",
        "PHONE_PROVIDER": f"Phone provider name. Available options: {','.join(list(settings.PHONE_PROVIDERS.keys()))}",
        "ZVONOK_API_KEY": "API public key. You can get it in Profile->Settings section.",
        "ZVONOK_CAMPAIGN_ID": "Calls by API campaign ID. You can get it after campaign creation.",
        "ZVONOK_AUDIO_ID": "Calls with specific audio. You can get it in Audioclips section.",
        "ZVONOK_SPEAKER_ID": "Calls with speaker.",
        "ZVONOK_POSTBACK_CALL_ID": "'Postback' call id (ct_call_id) query parameter name to validate a postback request.",
        "ZVONOK_POSTBACK_CAMPAIGN_ID": "'Postback' company id (ct_campaign_id) query parameter name to validate a postback request.",
        "ZVONOK_POSTBACK_STATUS": "'Postback' status (ct_status) query parameter name to validate a postback request.",
        "ZVONOK_POSTBACK_USER_CHOICE": "'Postback' user choice (ct_user_choice) query parameter name (optional).",
        "ZVONOK_POSTBACK_USER_CHOICE_ACK": "'Postback' user choice (ct_user_choice) query parameter value for acknowledge alert group (optional).",
        "ZVONOK_VERIFICATION_CAMPAIGN_ID": "The phone number verification campaign ID. You can get it after verification campaign creation.",
        "EXOTEL_ACCOUNT_SID": "Exotel account SID. You can get it in DEVELOPER SETTINGS -> API Settings",
        "EXOTEL_API_KEY": "API Key (username)",
        "EXOTEL_API_TOKEN": "API Token (password)",
        "EXOTEL_APP_ID": "Identifier of the flow (or applet)",
        "EXOTEL_CALLER_ID": "Exophone / Exotel virtual number",
        "EXOTEL_SMS_SENDER_ID": "Exotel SMS Sender ID to use for verification SMS",
        "EXOTEL_SMS_VERIFICATION_TEMPLATE": "SMS text template to be used for sending SMS, add $verification_code as a placeholder for the verification code",
        "EXOTEL_SMS_DLT_ENTITY_ID": "DLT Entity ID registered with TRAI.",
    }

    SECRET_SETTING_NAMES = (
        "EMAIL_HOST_PASSWORD",
        "INBOUND_EMAIL_WEBHOOK_SECRET",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_API_KEY_SID",
        "TWILIO_API_KEY_SECRET",
        "TWILIO_VERIFY_SERVICE_SID",
        "SLACK_CLIENT_OAUTH_ID",
        "SLACK_CLIENT_OAUTH_SECRET",
        "SLACK_SIGNING_SECRET",
        "TELEGRAM_TOKEN",
        "GRAFANA_CLOUD_ONCALL_TOKEN",
        "ZVONOK_API_KEY",
        "EXOTEL_ACCOUNT_SID",
        "EXOTEL_API_TOKEN",
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
        if len(setting_names_to_populate) == 0:
            return

        for setting_name in setting_names_to_populate:
            try:
                cls.objects.create(name=setting_name, value=cls._get_setting_from_setting_file(setting_name))
            except IntegrityError:
                # prevent the rare case where concurrent requests try inserting the same live setting and lead to:
                # django.db.utils.IntegrityError: duplicate key value violates unique constraint "base_livesetting_name_key"
                # this infers that a setting with this name already exists, and we can safely skip this
                continue

        cls.validate_settings()

    @classmethod
    def validate_settings(cls):
        settings_to_validate = cls.objects.filter(name__in=cls.AVAILABLE_NAMES)
        for setting in settings_to_validate:
            setting.error = LiveSettingValidator(live_setting=setting).get_error()
            setting.save(update_fields=["error"])

    @staticmethod
    def _get_setting_from_setting_file(setting_name):
        return getattr(settings, setting_name)

    def save(self, *args, **kwargs):
        if self.name not in self.AVAILABLE_NAMES:
            raise ValueError(
                f"Setting with name '{self.name}' is not in list of available names {self.AVAILABLE_NAMES}"
            )

        super().save(*args, **kwargs)
