from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def calculate_escalation_finish_time(alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk)[0]
    if alert_group.escalation_snapshot:
        alert_group.estimate_escalation_finish_time = alert_group.calculate_eta_for_finish_escalation()
        alert_group.save(update_fields=["estimate_escalation_finish_time"])
