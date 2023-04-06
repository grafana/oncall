import logging

from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = logging.getLogger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def custom_webhook_result(webhook_pk, alert_group_pk, escalation_policy_pk=None):
    from apps.webhooks.tasks import execute_webhook

    execute_webhook.apply_async((webhook_pk, alert_group_pk, None, escalation_policy_pk))
