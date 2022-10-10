from smtplib import SMTPException
from socket import gaierror

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import BadHeaderError, get_connection, send_mail
from django.utils.html import strip_tags

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.email.alert_rendering import build_subject_and_title
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

MAX_RETRIES = 1 if settings.DEBUG else 10
logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def notify_user_async(user_pk, alert_group_pk, notification_policy_pk):
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} does not exist")
        return

    try:
        alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} does not exist")
        return

    try:

        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"User notification policy {notification_policy_pk} does not exist")
        return

    subject, html_message = build_subject_and_title(alert_group)

    message = strip_tags(html_message)
    email_from = settings.EMAIL_HOST_USER
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
        # send email through Django setup
        send_mail(subject, message, email_from, recipient_list, html_message=html_message, connection=connection)
    except (gaierror, SMTPException, BadHeaderError, TimeoutError) as e:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Email sending error",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
            notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_DELIVERY_FAILED,
        )
        logger.error(f"Error sending email message: {e}")
        return
