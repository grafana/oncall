import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from rest_framework import status

from apps.alerts.models import Alert
from apps.mattermost.alert_rendering import MattermostMessageRenderer
from apps.mattermost.client import MattermostClient
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid
from apps.mattermost.models import MattermostChannel, MattermostMessage
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

    message = alert_group.mattermost_messages.filter(message_type=MattermostMessage.ALERT_GROUP_MESSAGE).first()
    if message:
        logger.error(f"Mattermost message exist with post id {message.post_id} hence skipping")
        return

    mattermost_channel = MattermostChannel.get_channel_for_alert_group(alert_group=alert_group)
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
