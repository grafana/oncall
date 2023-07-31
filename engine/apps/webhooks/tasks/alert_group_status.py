import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.webhooks.models import Webhook
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .trigger_webhook import send_webhook_event

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


MAX_RETRIES = 10

ACTION_TO_TRIGGER_TYPE = {
    AlertGroupLogRecord.TYPE_ACK: Webhook.TRIGGER_ACKNOWLEDGE,
    AlertGroupLogRecord.TYPE_RESOLVED: Webhook.TRIGGER_RESOLVE,
    AlertGroupLogRecord.TYPE_SILENCE: Webhook.TRIGGER_SILENCE,
    AlertGroupLogRecord.TYPE_UN_SILENCE: Webhook.TRIGGER_UNSILENCE,
    AlertGroupLogRecord.TYPE_UN_RESOLVED: Webhook.TRIGGER_UNRESOLVE,
    AlertGroupLogRecord.TYPE_UN_ACK: Webhook.TRIGGER_UNACKNOWLEDGE,
}


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_created(self, alert_group_id):
    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_id)
    except AlertGroup.DoesNotExist:
        return

    trigger_type = Webhook.TRIGGER_ALERT_GROUP_CREATED
    organization_id = alert_group.channel.organization_id
    webhooks = Webhook.objects.filter(trigger_type=trigger_type, organization_id=organization_id)

    # check if there are any webhooks before going on
    if not webhooks:
        return

    send_webhook_event.apply_async((trigger_type, alert_group_id), kwargs={"organization_id": organization_id})


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_status_change(self, action_type, alert_group_id, user_id):
    try:
        alert_group = AlertGroup.objects.get(pk=alert_group_id)
    except AlertGroup.DoesNotExist:
        return

    trigger_type = ACTION_TO_TRIGGER_TYPE.get(action_type)
    if trigger_type is None:
        return

    organization_id = alert_group.channel.organization_id
    webhooks = Webhook.objects.filter(trigger_type=trigger_type, organization_id=organization_id)

    # check if there are any webhooks before going on
    if not webhooks:
        return

    send_webhook_event.apply_async(
        (trigger_type, alert_group_id),
        kwargs={"organization_id": organization_id, "user_id": user_id},
    )
