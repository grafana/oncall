import logging

import requests
from django.apps import apps
from django.conf import settings
from django.db import models
from rest_framework import status
from twilio.base.exceptions import TwilioRestException

from apps.alerts.constants import ActionSource
from apps.alerts.incident_appearance.renderers.phone_call_renderer import AlertGroupPhoneCallRenderer
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.utils import live_settings
from apps.twilioapp.constants import TwilioCallStatuses
from apps.twilioapp.twilio_client import twilio_client
from apps.twilioapp.asterisk_client import asterisk_client

from common.api_helpers.utils import create_engine_url
from common.utils import clean_markup, escape_for_twilio_phone_call

logger = logging.getLogger(__name__)


class PhoneCallManager(models.Manager):
    def update_status(self, call_sid, call_status):
        """The function checks existence of PhoneCall instance
        according to call_sid and updates status on message_status

        Args:
            call_sid (str): sid of Twilio call
            call_status (str): new status

        Returns:

        """
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        if call_sid and call_status:
            phone_call_qs = self.filter(sid=call_sid)

            status = TwilioCallStatuses.DETERMINANT.get(call_status)

            if phone_call_qs.exists() and status:
                phone_call_qs.update(status=status)
                phone_call = phone_call_qs.first()
                if phone_call.grafana_cloud_notification:
                    # If call was made via grafana twilio it is don't needed to create logs on it's delivery status.
                    return
                log_record = None
                if status == TwilioCallStatuses.COMPLETED:
                    log_record = UserNotificationPolicyLogRecord(
                        author=phone_call.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
                        notification_policy=phone_call.notification_policy,
                        alert_group=phone_call.represents_alert_group,
                        notification_step=phone_call.notification_policy.step
                        if phone_call.notification_policy
                        else None,
                        notification_channel=phone_call.notification_policy.notify_by
                        if phone_call.notification_policy
                        else None,
                    )
                elif status in [TwilioCallStatuses.FAILED, TwilioCallStatuses.BUSY, TwilioCallStatuses.NO_ANSWER]:
                    log_record = UserNotificationPolicyLogRecord(
                        author=phone_call.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                        notification_policy=phone_call.notification_policy,
                        alert_group=phone_call.represents_alert_group,
                        notification_error_code=PhoneCall.get_error_code_by_twilio_status(status),
                        notification_step=phone_call.notification_policy.step
                        if phone_call.notification_policy
                        else None,
                        notification_channel=phone_call.notification_policy.notify_by
                        if phone_call.notification_policy
                        else None,
                    )

                if log_record is not None:
                    log_record.save()
                    user_notification_action_triggered_signal.send(
                        sender=PhoneCall.objects.update_status, log_record=log_record
                    )

    def get_and_process_digit(self, call_sid, digit):
        """The function get Phone Call instance according to call_sid
        and run process of pressed digit

        Args:
            call_sid (str):
            digit (str):

        Returns:

        """
        if call_sid and digit:
            phone_call = self.filter(sid=call_sid).first()

            if phone_call:
                phone_call.process_digit(digit=digit)


class PhoneCall(models.Model):

    objects = PhoneCallManager()

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey("alerts.Alert", on_delete=models.SET_NULL, null=True, default=None)
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.CASCADE, null=True, default=None)

    status = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        choices=TwilioCallStatuses.CHOICES,
    )

    sid = models.CharField(
        blank=True,
        max_length=50,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    grafana_cloud_notification = models.BooleanField(default=False)

    class PhoneCallsLimitExceeded(Exception):
        """Phone calls limit exceeded"""

    class PhoneNumberNotVerifiedError(Exception):
        """Phone number is not verified"""

    class CloudSendError(Exception):
        """Error making call through cloud"""

    def process_digit(self, digit):
        """The function process pressed digit at time of call to user

        Args:
            digit (str):

        Returns:

        """
        alert_group = self.represents_alert_group

        if digit == "1":
            alert_group.acknowledge_by_user(self.receiver, action_source=ActionSource.TWILIO)
        elif digit == "2":
            alert_group.resolve_by_user(self.receiver, action_source=ActionSource.TWILIO)
        elif digit == "3":
            alert_group.silence_by_user(self.receiver, silence_delay=1800, action_source=ActionSource.TWILIO)

    @property
    def created_for_slack(self):
        return bool(self.represents_alert_group.slack_message)

    @classmethod
    def _make_cloud_call(cls, user, message_body):
        url = create_engine_url("api/v1/make_call", override_base=settings.GRAFANA_CLOUD_ONCALL_API_URL)
        auth = {"Authorization": live_settings.GRAFANA_CLOUD_ONCALL_TOKEN}
        data = {
            "email": user.email,
            "message": message_body,
        }
        try:
            response = requests.post(url, headers=auth, data=data, timeout=5)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Unable to make call through cloud. Request exception {str(e)}")
            raise PhoneCall.CloudSendError("Unable to make call through cloud: request failed")
        if response.status_code == status.HTTP_200_OK:
            logger.info("Make cloud call successfully")
        if response.status_code == status.HTTP_400_BAD_REQUEST and response.json().get("error") == "limit-exceeded":
            raise PhoneCall.PhoneCallsLimitExceeded("Organization calls limit exceeded")
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            raise PhoneCall.CloudSendError("Unable to make call through cloud: user not found")
        else:
            raise PhoneCall.CloudSendError("Unable to make call through cloud: server error")

    @classmethod
    def make_call(cls, user, alert_group, notification_policy, is_cloud_notification=False):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
        log_record = None
        renderer = AlertGroupPhoneCallRenderer(alert_group)
        message_body = renderer.render()
        try:
            if is_cloud_notification:
                cls._make_cloud_call(user, message_body)
            else:
                cls._make_call(user, message_body, alert_group=alert_group, notification_policy=notification_policy)
        except (TwilioRestException, PhoneCall.CloudSendError):
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except PhoneCall.PhoneCallsLimitExceeded:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except PhoneCall.PhoneNumberNotVerifiedError:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )

        if log_record is not None:
            log_record.save()
            user_notification_action_triggered_signal.send(sender=PhoneCall.make_call, log_record=log_record)

    @classmethod
    def make_grafana_cloud_call(cls, user, message_body):
        message_body = escape_for_twilio_phone_call(clean_markup(message_body))
        cls._make_call(user, message_body, grafana_cloud=True)

    @classmethod
    def _make_call(cls, user, message_body, alert_group=None, notification_policy=None, grafana_cloud=False):
        if live_settings.PHONE_PROVIDER == "Asterisk":
            asterisk_client.make_call(message_body, user.verified_phone_number)
        else:
            if not user.verified_phone_number:
                raise PhoneCall.PhoneNumberNotVerifiedError("User phone number is not verified")

            phone_call = PhoneCall(
                represents_alert_group=alert_group,
                receiver=user,
                notification_policy=notification_policy,
                grafana_cloud_notification=grafana_cloud,
            )
            phone_calls_left = user.organization.phone_calls_left(user)

            if phone_calls_left <= 0:
                phone_call.exceeded_limit = True
                phone_call.save()
                raise PhoneCall.PhoneCallsLimitExceeded("Organization calls limit exceeded")

            phone_call.exceeded_limit = False
            if phone_calls_left < 3:
                message_body += " {} phone calls left. Contact your admin.".format(phone_calls_left)

            twilio_call = twilio_client.make_call(message_body, user.verified_phone_number, grafana_cloud=grafana_cloud)
            if twilio_call.status and twilio_call.sid:
                phone_call.status = TwilioCallStatuses.DETERMINANT.get(twilio_call.status, None)
                phone_call.sid = twilio_call.sid
            phone_call.save()

            return phone_call

    @staticmethod
    def get_error_code_by_twilio_status(status):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
            TwilioCallStatuses.BUSY: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_LINE_BUSY,
            TwilioCallStatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_FAILED,
            TwilioCallStatuses.NO_ANSWER: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_NO_ANSWER,
        }

        return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)
