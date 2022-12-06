import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.public_api.serializers import IncidentSerializer
from apps.webhooks.models import Webhook
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .send_webhook_event import send_webhook_event

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


MAX_RETRIES = 10


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_created(self, alert_group_id):
    logger.error("CREATED AG ID: %s", alert_group_id)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else MAX_RETRIES
)
def alert_group_status_change(self, action_type, alert_group_id, user_id):
    # TODO: update mapping, maybe use a dict instead
    if action_type == AlertGroupLogRecord.TYPE_ACK:
        trigger_type = Webhook.TRIGGER_ACKNOWLEDGE
    elif action_type == AlertGroupLogRecord.TYPE_RESOLVED:
        trigger_type = Webhook.TRIGGER_RESOLVE
    elif action_type == AlertGroupLogRecord.TYPE_SILENCE:
        trigger_type = Webhook.TRIGGER_SILENCE
    else:
        return

    try:
        alert_group = AlertGroup.unarchived_objects.get(pk=alert_group_id)
    except AlertGroup.DoesNotExist:
        return

    data = IncidentSerializer(alert_group).data
    # {'id': 'IPLUY9ZTUSFRB',
    #  'integration_id': 'C54JCV176PLAT',
    #  'route_id': 'R7PA8YB9RKAQH',
    #  'alerts_count': 1,
    #  'state': 'acknowledged',
    #  'created_at': '2022-12-05T19:28:01.057997Z',
    #  'resolved_at': None,
    #  'acknowledged_at': '2022-12-06T01:53:52.454569Z',
    #  'title': 'Demo alert',
    #  'permalinks': {'slack': None, 'telegram': None}
    # }

    # TODO: not really sure what user_id or team_id should be?
    organization_id = alert_group.channel.organization_id
    send_webhook_event.apply_async((trigger_type, data), {"org_id": organization_id})
