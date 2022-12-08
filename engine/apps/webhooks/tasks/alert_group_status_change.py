import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.user_management.models import User
from apps.webhooks.models import Webhook
from apps.webhooks.utils import serialize_event
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .send_webhook_event import send_webhook_event

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


MAX_RETRIES = 10


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_created(self, alert_group_id):
    try:
        alert_group = AlertGroup.unarchived_objects.get(pk=alert_group_id)
    except AlertGroup.DoesNotExist:
        return

    trigger_type = Webhook.TRIGGER_NEW
    event = {
        "type": "Firing",
        "time": alert_group.started_at,
    }
    data = serialize_event(event, alert_group, None)
    organization_id = alert_group.channel.organization_id
    send_webhook_event.apply_async((trigger_type, data), kwargs={"org_id": organization_id})


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_status_change(self, action_type, alert_group_id, user_id):
    try:
        alert_group = AlertGroup.unarchived_objects.get(pk=alert_group_id)
        user = User.objects.get(pk=user_id)
    except (AlertGroup.DoesNotExist, User.DoesNotExist):
        return

    # TODO: update mapping, maybe use a dict instead
    if action_type == AlertGroupLogRecord.TYPE_ACK:
        trigger_type = Webhook.TRIGGER_ACKNOWLEDGE
        event = {
            "type": "Acknowledge",
            "time": alert_group.acknowledged_at,
        }
    elif action_type == AlertGroupLogRecord.TYPE_RESOLVED:
        trigger_type = Webhook.TRIGGER_RESOLVE
        event = {
            "type": "Resolve",
            "time": alert_group.resolved_at,
        }
    elif action_type == AlertGroupLogRecord.TYPE_SILENCE:
        trigger_type = Webhook.TRIGGER_SILENCE
        event = {
            "type": "Silence",
            "time": alert_group.silenced_at,
            "until": alert_group.silenced_until,
        }
    elif action_type == AlertGroupLogRecord.TYPE_UN_SILENCE:
        trigger_type = Webhook.TRIGGER_UNSILENCE
        event = {
            "type": "Unsilence",
        }
    elif action_type == AlertGroupLogRecord.TYPE_UN_RESOLVED:
        trigger_type = Webhook.TRIGGER_UNRESOLVE
        event = {
            "type": "Unresolve",
        }
    else:
        return

    data = serialize_event(event, alert_group, user)
    organization_id = alert_group.channel.organization_id
    send_webhook_event.apply_async((trigger_type, data), kwargs={"org_id": organization_id})
