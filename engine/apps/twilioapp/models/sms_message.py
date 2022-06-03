import logging

from django.apps import apps
from django.db import models
from twilio.base.exceptions import TwilioRestException

from apps.alerts.incident_appearance.renderers.sms_renderer import AlertGroupSmsRenderer
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.twilioapp.constants import TwilioMessageStatuses
from apps.twilioapp.twilio_client import twilio_client

logger = logging.getLogger(__name__)


class SMSMessageManager(models.Manager):
    def update_status(self, message_sid, message_status):
        """The function checks existence of SMSMessage
        instance according to message_sid and updates status on
        message_status

        Args:
            message_sid (str): sid of Twilio message
            message_status (str): new status

        Returns:

        """
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        if message_sid and message_status:
            sms_message_qs = self.filter(sid=message_sid)

            status = TwilioMessageStatuses.DETERMINANT.get(message_status)

            if sms_message_qs.exists() and status:
                sms_message_qs.update(status=status)

                sms_message = sms_message_qs.first()
                if sms_message.grafana_cloud_notification:
                    # If sms was sent via grafana twilio it is don't needed to create logs on it's delivery status.
                    return
                log_record = None

                if status == TwilioMessageStatuses.DELIVERED:
                    log_record = UserNotificationPolicyLogRecord(
                        author=sms_message.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
                        notification_policy=sms_message.notification_policy,
                        alert_group=sms_message.represents_alert_group,
                        notification_step=sms_message.notification_policy.step
                        if sms_message.notification_policy
                        else None,
                        notification_channel=sms_message.notification_policy.notify_by
                        if sms_message.notification_policy
                        else None,
                    )
                elif status in [TwilioMessageStatuses.UNDELIVERED, TwilioMessageStatuses.FAILED]:
                    log_record = UserNotificationPolicyLogRecord(
                        author=sms_message.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                        notification_policy=sms_message.notification_policy,
                        alert_group=sms_message.represents_alert_group,
                        notification_error_code=sms_message.get_error_code_by_twilio_status(status),
                        notification_step=sms_message.notification_policy.step
                        if sms_message.notification_policy
                        else None,
                        notification_channel=sms_message.notification_policy.notify_by
                        if sms_message.notification_policy
                        else None,
                    )
                if log_record is not None:
                    log_record.save()
                    user_notification_action_triggered_signal.send(
                        sender=SMSMessage.objects.update_status, log_record=log_record
                    )


class SMSMessage(models.Model):
    objects = SMSMessageManager()

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
        choices=TwilioMessageStatuses.CHOICES,
    )
    grafana_cloud_notification = models.BooleanField(default=False)

    # https://www.twilio.com/docs/sms/api/message-resource#message-properties
    sid = models.CharField(
        blank=True,
        max_length=50,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class SMSLimitExceeded(Exception):
        """SMS limit exceeded"""

    class PhoneNumberNotVerifiedError(Exception):
        """Phone number is not verified"""

    @property
    def created_for_slack(self):
        return bool(self.represents_alert_group.slack_message)

    @classmethod
    def send_sms(cls, user, alert_group, notification_policy):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        log_record = None
        renderer = AlertGroupSmsRenderer(alert_group)
        message_body = renderer.render()
        try:
            cls._send_sms(user, message_body, alert_group=alert_group, notification_policy=notification_policy)
        except TwilioRestException:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except SMSMessage.SMSLimitExceeded:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
        except SMSMessage.PhoneNumberNotVerifiedError:
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
            user_notification_action_triggered_signal.send(sender=SMSMessage.send_sms, log_record=log_record)

    @classmethod
    def send_grafana_cloud_sms(cls, user, message_body):
        cls._send_sms(user, message_body, grafana_cloud=True)

    @classmethod
    def _send_sms(cls, user, message_body, alert_group=None, notification_policy=None, grafana_cloud=False):
        if not user.verified_phone_number:
            raise SMSMessage.PhoneNumberNotVerifiedError("User phone number is not verified")

        sms_message = SMSMessage(
            represents_alert_group=alert_group,
            receiver=user,
            notification_policy=notification_policy,
            grafana_cloud_notification=grafana_cloud,
        )
        sms_left = user.organization.sms_left(user)

        if sms_left <= 0:
            sms_message.exceeded_limit = True
            sms_message.save()
            raise SMSMessage.SMSLimitExceeded("Organization sms limit exceeded")

        sms_message.exceeded_limit = False
        if sms_left < 3:
            message_body += " {} sms left. Contact your admin.".format(sms_left)

        twilio_message = twilio_client.send_message(message_body, user.verified_phone_number)
        if twilio_message.status and twilio_message.sid:
            sms_message.status = TwilioMessageStatuses.DETERMINANT.get(twilio_message.status, None)
            sms_message.sid = twilio_message.sid
        sms_message.save()

        return sms_message

    @staticmethod
    def get_error_code_by_twilio_status(status):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
            TwilioMessageStatuses.UNDELIVERED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
            TwilioMessageStatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
        }

        return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)
