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

    # https://www.twilio.com/docs/sms/api/message-resource#message-properties
    sid = models.CharField(
        blank=True,
        max_length=50,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def created_for_slack(self):
        return bool(self.represents_alert_group.slack_message)

    @classmethod
    def send_sms(cls, user, alert_group, notification_policy):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        organization = alert_group.channel.organization

        log_record = None
        if user.verified_phone_number:
            # Create an SMS object in db
            sms_message = SMSMessage(
                represents_alert_group=alert_group, receiver=user, notification_policy=notification_policy
            )

            sms_left = organization.sms_left(user)
            if sms_left > 0:
                # Mark is as successfully sent
                sms_message.exceeded_limit = False
                # Render alert message for sms
                renderer = AlertGroupSmsRenderer(alert_group)
                message_body = renderer.render()
                # Notify if close to limit
                if sms_left < 3:
                    message_body += " {} sms left. Contact your admin.".format(sms_left)
                # Send an sms
                try:
                    twilio_message = twilio_client.send_message(message_body, user.verified_phone_number)
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
                else:
                    if twilio_message.status and twilio_message.sid:
                        sms_message.status = TwilioMessageStatuses.DETERMINANT.get(twilio_message.status, None)
                        sms_message.sid = twilio_message.sid
            else:
                # If no more sms left, mark as exceeded limit
                log_record = UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    alert_group=alert_group,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED,
                    notification_step=notification_policy.step if notification_policy else None,
                    notification_channel=notification_policy.notify_by if notification_policy else None,
                )
                sms_message.exceeded_limit = True

            # Save object
            sms_message.save()
        else:
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

    @staticmethod
    def get_error_code_by_twilio_status(status):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        TWILIO_ERRORS_TO_ERROR_CODES_MAP = {
            TwilioMessageStatuses.UNDELIVERED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
            TwilioMessageStatuses.FAILED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
        }

        return TWILIO_ERRORS_TO_ERROR_CODES_MAP.get(status, None)
