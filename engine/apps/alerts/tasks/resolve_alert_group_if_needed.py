# TODO: remove this file when all the resolve_alert_group_if_needed are processed
# New version - apps.alerts.tasks.resolve_alert_group_by_source_if_needed.resolve_alert_group_by_source_if_needed

from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def resolve_alert_group_if_needed(alert_id):
    """
    The purpose of this task is to avoid computation-heavy check after each alert.
    Should be delayed and invoked only for the last one.
    """
    AlertGroupForAlertManager = apps.get_model("alerts", "AlertGroupForAlertManager")
    AlertForAlertManager = apps.get_model("alerts", "AlertForAlertManager")

    alert = AlertForAlertManager.objects.get(pk=alert_id)
    if not resolve_alert_group_if_needed.request.id == alert.group.active_resolve_calculation_id:
        return "Resolve calculation celery ID mismatch. Duplication or non-active. Active: {}".format(
            alert.group.active_resolve_calculation_id
        )
    else:
        # Retrieving group again to have an access to child class methods
        alert_group = AlertGroupForAlertManager.all_objects.get(pk=alert.group_id)
        if alert_group.is_alert_a_resolve_signal(alert):
            alert_group.resolve_by_source()
            return f"resolved alert_group {alert_group.pk}"
