import logging
import uuid

from django.apps import apps
from django.db import models
from python_http_client.exceptions import BadRequestsError, ForbiddenError, UnauthorizedError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import CustomArg, Mail

from apps.alerts.incident_appearance.renderers.email_renderer import AlertGroupEmailRenderer
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.base.utils import live_settings
from apps.sendgridapp.constants import SendgridEmailMessageStatuses

logger = logging.getLogger(__name__)


class EmailMessageManager(models.Manager):
    def update_status(self, message_uuid, message_status):
        """The function checks existence of EmailMessage
        instance according to message_uuid and updates status on
        message_status

        Args:
            message_uuid (str): uuid of Email message
            message_status (str): new status

        Returns:

        """
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        if message_uuid and message_status:
            email_message_qs = self.filter(message_uuid=message_uuid)
            status = SendgridEmailMessageStatuses.DETERMINANT.get(message_status)

            if email_message_qs.exists() and status:
                email_message_qs.update(status=status)

                email_message = email_message_qs.first()
                log_record = None

                if status == SendgridEmailMessageStatuses.DELIVERED:
                    log_record = UserNotificationPolicyLogRecord(
                        author=email_message.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
                        notification_policy=email_message.notification_policy,
                        alert_group=email_message.represents_alert_group,
                        notification_step=email_message.notification_policy.step
                        if email_message.notification_policy
                        else None,
                        notification_channel=email_message.notification_policy.notify_by
                        if email_message.notification_policy
                        else None,
                    )
                elif status in [
                    SendgridEmailMessageStatuses.BOUNCE,
                    SendgridEmailMessageStatuses.BLOCKED,
                    SendgridEmailMessageStatuses.DROPPED,
                ]:
                    log_record = UserNotificationPolicyLogRecord(
                        author=email_message.receiver,
                        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                        notification_policy=email_message.notification_policy,
                        alert_group=email_message.represents_alert_group,
                        notification_error_code=email_message.get_error_code_by_sendgrid_status(status),
                        notification_step=email_message.notification_policy.step
                        if email_message.notification_policy
                        else None,
                        notification_channel=email_message.notification_policy.notify_by
                        if email_message.notification_policy
                        else None,
                    )
                if log_record is not None:
                    log_record.save()
                    user_notification_action_triggered_signal.send(
                        sender=EmailMessage.objects.update_status, log_record=log_record
                    )


class EmailMessage(models.Model):
    objects = EmailMessageManager()

    message_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    exceeded_limit = models.BooleanField(null=True, default=None)
    represents_alert = models.ForeignKey("alerts.Alert", on_delete=models.SET_NULL, null=True, default=None)
    represents_alert_group = models.ForeignKey("alerts.AlertGroup", on_delete=models.SET_NULL, null=True, default=None)
    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, null=True, default=None
    )

    receiver = models.ForeignKey("user_management.User", on_delete=models.PROTECT, null=True, default=None)

    status = models.PositiveSmallIntegerField(blank=True, null=True, choices=SendgridEmailMessageStatuses.CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def send_incident_mail(user, alert_group, notification_policy):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        log_record = None
        alert = alert_group.alerts.first()

        email_message = EmailMessage(
            represents_alert_group=alert_group,
            represents_alert=alert,
            receiver=user,
            notification_policy=notification_policy,
        )
        emails_left = alert_group.channel.organization.emails_left(user)
        if emails_left > 0:
            email_message.exceeded_limit = False

            limit_notification = False
            if emails_left < 5:
                limit_notification = True

            subject, html_content = AlertGroupEmailRenderer(alert_group).render(limit_notification)

            message = Mail(
                from_email=live_settings.SENDGRID_FROM_EMAIL,
                to_emails=user.email,
                subject=subject,
                html_content=html_content,
            )
            custom_arg = CustomArg("message_uuid", str(email_message.message_uuid))
            message.add_custom_arg(custom_arg)

            sendgrid_client = SendGridAPIClient(live_settings.SENDGRID_API_KEY)
            try:
                response = sendgrid_client.send(message)
                sending_status = True
            except (BadRequestsError, UnauthorizedError, ForbiddenError) as e:
                logger.error(f"Error email sending: {e}")
                sending_status = False
            else:
                if response.status_code == 202:
                    email_message.status = SendgridEmailMessageStatuses.ACCEPTED
                    email_message.save()
                else:
                    logger.error(f"Error email sending: status code: {response.status_code}")
                    sending_status = False

            if not sending_status:
                log_record = UserNotificationPolicyLogRecord(
                    author=user,
                    type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                    notification_policy=notification_policy,
                    alert_group=alert_group,
                    notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_MAIL,
                    notification_step=notification_policy.step if notification_policy else None,
                    notification_channel=notification_policy.notify_by if notification_policy else None,
                )
        else:
            log_record = UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED,
                notification_step=notification_policy.step if notification_policy else None,
                notification_channel=notification_policy.notify_by if notification_policy else None,
            )
            email_message.exceeded_limit = True
            email_message.save()

        if log_record is not None:
            log_record.save()
            user_notification_action_triggered_signal.send(
                sender=EmailMessage.send_incident_mail, log_record=log_record
            )

    @staticmethod
    def get_error_code_by_sendgrid_status(status):
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        SENDGRID_ERRORS_TO_ERROR_CODES_MAP = {
            SendgridEmailMessageStatuses.BOUNCE: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_DELIVERY_FAILED,
            SendgridEmailMessageStatuses.BLOCKED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_DELIVERY_FAILED,
            SendgridEmailMessageStatuses.DROPPED: UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_DELIVERY_FAILED,
        }

        return SENDGRID_ERRORS_TO_ERROR_CODES_MAP.get(status, None)
