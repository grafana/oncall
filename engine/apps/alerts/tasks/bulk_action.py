from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def bulk_alert_group_action(action_name, delay, alert_group_public_pks, user_pk, organization_id):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    User = apps.get_model("user_management", "User")

    alert_groups = AlertGroup.unarchived_objects.filter(
        channel__organization_id=organization_id, public_primary_key__in=alert_group_public_pks
    )

    kwargs = {}
    if action_name == AlertGroup.SILENCE:
        kwargs["silence_delay"] = delay
    kwargs["user"] = User.objects.get(pk=user_pk)
    kwargs["alert_groups"] = alert_groups

    method = getattr(AlertGroup, f"bulk_{action_name}")
    method(**kwargs)
