import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from rest_framework import status

from apps.alerts.models import Alert, AlertGroup
from apps.mattermost.alert_rendering import AlertGroupMattermostRenderer, MattermostMessageRenderer
from apps.mattermost.client import MattermostClient
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid
from apps.mattermost.models import MattermostChannel, MattermostMessage
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import OkToRetry

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_create_alert_async(self, alert_pk):
    """
    It's async in order to prevent Mattermost downtime or formatting issues causing delay with SMS and other destinations.
    """
    try:
        alert = Alert.objects.get(pk=alert_pk)
    except Alert.DoesNotExist as e:
        if on_create_alert_async.request.retries >= 10:
            logger.error(f"Alert {alert_pk} was not found. Probably it was deleted. Stop retrying")
            return
        else:
            raise e

    alert_group = alert.group
    mattermost_channel = MattermostChannel.get_channel_for_alert_group(alert_group=alert_group)
    if not mattermost_channel:
        logger.error(f"Mattermost channel not found for alert {alert_pk}. Probably it was deleted. Stop retrying")
        return

    message = alert_group.mattermost_messages.filter(message_type=MattermostMessage.ALERT_GROUP_MESSAGE).first()
    if message:
        logger.error(f"Mattermost message exist with post id {message.post_id} hence skipping")
        return

    payload = MattermostMessageRenderer(alert_group).render_alert_group_message()

    with OkToRetry(task=self, exc=(MattermostAPIException,), num_retries=3):
        try:
            client = MattermostClient()
            mattermost_post = client.create_post(channel_id=mattermost_channel.channel_id, data=payload)
        except MattermostAPITokenInvalid:
            logger.error(f"Mattermost API token is invalid could not create post for alert {alert_pk}")
        except MattermostAPIException as ex:
            logger.error(f"Mattermost API error {ex}")
            if ex.status not in [status.HTTP_401_UNAUTHORIZED]:
                raise ex
        else:
            MattermostMessage.create_message(
                alert_group=alert_group, post=mattermost_post, message_type=MattermostMessage.ALERT_GROUP_MESSAGE
            )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_alert_group_action_triggered_async(log_record_id):
    from apps.alerts.models import AlertGroupLogRecord
    from apps.mattermost.alert_group_representative import AlertGroupMattermostRepresentative

    try:
        log_record = AlertGroupLogRecord.objects.get(pk=log_record_id)
    except AlertGroupLogRecord.DoesNotExist as e:
        logger.warning(f"Mattermost representative: log record {log_record_id} never created or has been deleted")
        raise e

    alert_group_id = log_record.alert_group_id

    try:
        log_record.alert_group.mattermost_messages.get(message_type=MattermostMessage.ALERT_GROUP_MESSAGE)
    except MattermostMessage.DoesNotExist as e:
        if on_alert_group_action_triggered_async.request.retries >= 10:
            logger.error(f"Mattermost message not created for {alert_group_id}. Stop retrying")
            return
        else:
            raise e

    logger.info(
        f"Start mattermost on_alert_group_action_triggered for alert_group {alert_group_id}, log record {log_record_id}"
    )
    representative = AlertGroupMattermostRepresentative(log_record)
    if representative.is_applicable():
        handler = representative.get_handler()
        handler(log_record.alert_group)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_user_about_alert_async(user_pk, alert_group_pk, notification_policy_pk):
    from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

    def _create_error_log_record(notification_error_code=None):
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            reason="Error during mattermost notification",
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
            notification_error_code=notification_error_code,
        )

    try:
        user = User.objects.get(pk=user_pk)
        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
        notification_policy = UserNotificationPolicy.objects.get(pk=notification_policy_pk)
        mattermost_messsage = alert_group.mattermost_messages.get(message_type=MattermostMessage.ALERT_GROUP_MESSAGE)
    except User.DoesNotExist:
        logger.warning(f"User {user_pk} is not found")
        return
    except AlertGroup.DoesNotExist:
        logger.warning(f"Alert group {alert_group_pk} is not found")
        return
    except UserNotificationPolicy.DoesNotExist:
        logger.warning(f"UserNotificationPolicy {notification_policy_pk} is not found")
        return
    except MattermostMessage.DoesNotExist as e:
        if notify_user_about_alert_async.request.retries >= 10:
            logger.error(
                f"Alert group mattermost message is not created {alert_group_pk}. Hence stopped retrying for user notification"
            )
            _create_error_log_record(
                UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_MATTERMOST_ALERT_GROUP_MESSAGE_NOT_FOUND
            )
            return
        else:
            raise e

    mattermost_channel = MattermostChannel.get_channel_for_alert_group(alert_group=alert_group)
    if not mattermost_channel:
        logger.error(f"Mattermost channel not found for user notification {user_pk}")
        return

    templated_alert = AlertGroupMattermostRenderer(alert_group).alert_renderer.templated_alert

    print("Check identity")
    if not hasattr(user, "mattermost_user_identity"):
        message = "{}\nTried to invite {} to look at the alert group. Unfortunately {} is not in mattermost.".format(
            templated_alert.title, user.username, user.username
        )
        _create_error_log_record(
            UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_MATTERMOST_USER_NOT_IN_MATTERMOST
        )
    else:
        message = "{}\nInviting {} to look at the alert group.".format(
            templated_alert.title, user.mattermost_user_identity.mention_username
        )

    payload = {"root_id": mattermost_messsage.post_id, "message": message}

    try:
        client = MattermostClient()
        client.create_post(channel_id=mattermost_channel.channel_id, data=payload)
    except MattermostAPITokenInvalid:
        logger.error(f"Mattermost API token is invalid could not create post for alert {alert_group_pk}")
        _create_error_log_record(UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_MATTERMOST_API_TOKEN_INVALID)
    except MattermostAPIException as ex:
        logger.error(f"Mattermost API error {ex}")
        if ex.status != status.HTTP_401_UNAUTHORIZED:
            raise ex
        _create_error_log_record(UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_MATTERMOST_API_UNAUTHORIZED)
    else:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_step=notification_policy.step,
            notification_channel=notification_policy.notify_by,
        )
