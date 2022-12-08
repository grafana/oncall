import logging

from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = logging.getLogger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def custom_webhook_result(alert_group_pk, escalation_policy_pk=None):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    Webhook = apps.get_model("webhooks", "Webhook")

    alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk)[0]

    from apps.webhooks.tasks import send_webhook_event
    from apps.webhooks.utils import serialize_event

    event = {"type": "Escalation"}
    data = serialize_event(event, alert_group, user=None)
    send_webhook_event.apply_async(
        (Webhook.TRIGGER_ESCALATION_STEP, data), kwargs={"org_id": alert_group.channel.organization_id}
    )

    # TODO: add log record
