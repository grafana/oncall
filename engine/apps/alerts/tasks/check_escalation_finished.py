from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.alerts.tasks.task_logger import task_logger
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None, default_retry_delay=60
)
def check_escalation_finished_task():
    """
    This task periodically checks if there are no alert groups with not finished escalations.
    TODO: QA this properly, check if new type of escalations had been added
    """
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

    CHECKING_TOLERANCE = timezone.timedelta(minutes=5)
    CHECKING_TIME = timezone.now() - CHECKING_TOLERANCE

    alert_groups = AlertGroup.all_objects.filter(
        ~Q(channel__integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE),
        ~Q(silenced=True, silenced_until__isnull=True),  # filter silenced forever alert_groups
        is_escalation_finished=False,
        resolved=False,
        acknowledged=False,
        root_alert_group=None,
        estimate_escalation_finish_time__lte=CHECKING_TIME,
    )

    if not alert_groups.exists():
        return

    exception_template = "Escalation for alert_group {} is not finished at expected time {}, now {}"

    now = timezone.now()
    exception_text = "\n".join(
        exception_template.format(alert_group.pk, alert_group.estimate_escalation_finish_time, now)
        for alert_group in alert_groups
    )

    ids = alert_groups.values_list("pk", flat=True)
    task_logger.debug(ids)

    raise Exception(exception_text)
