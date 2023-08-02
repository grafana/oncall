from socket import gaierror

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import BadHeaderError, get_connection, send_mail
from django.utils.html import strip_tags

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.email.alert_rendering import build_subject_and_message
from apps.email.models import EmailMessage
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


def get_from_email(user):
    if live_settings.EMAIL_FROM_ADDRESS:
        return live_settings.EMAIL_FROM_ADDRESS

    if settings.LICENSE == settings.CLOUD_LICENSE_NAME:
        return "oncall@{}.grafana.net".format(user.organization.stack_slug)

    return live_settings.EMAIL_HOST_USER


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk):
    # imported here to avoid circular import error
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} does not exist")
        return

    try:
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"User notification policy {notification_policy_pk} does not exist")
        return

    # create an error log in case EMAIL_HOST is not specified
    if not live_settings.EMAIL_HOST:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error while sending email",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        logger.error("Error while sending email: empty EMAIL_HOST env variable")
        return

    emails_left = user.organization.emails_left(user)
    if emails_left <= 0:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error while sending email",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
            notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED,
        )
        EmailMessage.objects.create(
            represents_alert_group=alert_group,
            notification_policy=notification_policy,
            receiver=user,
            exceeded_limit=True,
        )
        return

    subject, html_message = build_subject_and_message(alert_group, emails_left)

    message = strip_tags(html_message)
    from_email = get_from_email(user)
    recipient_list = [user.email]

    connection = get_connection(
        host=live_settings.EMAIL_HOST,
        port=live_settings.EMAIL_PORT,
        username=live_settings.EMAIL_HOST_USER,
        password=live_settings.EMAIL_HOST_PASSWORD,
        use_tls=live_settings.EMAIL_USE_TLS,
        fail_silently=False,
        timeout=5,
    )

    try:
        send_mail(subject, message, from_email, recipient_list, html_message=html_message, connection=connection)
        EmailMessage.objects.create(
            represents_alert_group=alert_group,
            notification_policy=notification_policy,
            receiver=user,
            exceeded_limit=False,
        )
    except (gaierror, BadHeaderError) as e:
        # gaierror is raised when EMAIL_HOST is invalid
        # BadHeaderError is raised when there's newlines in the subject
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error while sending email",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
        logger.error(f"Error while sending email: {e}")
        return
