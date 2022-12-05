import logging

from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_webhook_event(trigger_type, data, user_id=None, team_id=None, org_id=None):
    Webhooks = apps.get_model("webhooks", "Webhook")
    webhooks_qs = Webhooks.objects.filter(trigger_type=trigger_type, organization_id=org_id)
    if user_id:
        webhooks_qs = webhooks_qs.filter(user_id=user_id)
    if team_id:
        webhooks_qs = webhooks_qs.filter(team_id=team_id)

    for webhook in webhooks_qs:
        execute_webhook.apply_async((webhook.pk, data))


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def execute_webhook(webhook_pk, data):
    Webhooks = apps.get_model("webhooks", "Webhook")
    try:
        webhook = Webhooks.objects.get(pk=webhook_pk)
        if webhook.check_trigger(data):
            webhook.make_request(data)
        else:
            logger.info(f"Webhook {webhook_pk} trigger_template evaluated as false")
    except Webhooks.DoesNotExist:
        logger.warn(f"Webhook {webhook_pk} does not exist")
