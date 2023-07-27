from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def resolve_by_last_step_task(alert_group_pk):
    from apps.alerts.models import AlertGroup

    alert_group = AlertGroup.objects.get(pk=alert_group_pk)
    alert_group.resolve_by_last_step()
