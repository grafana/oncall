from django.conf import settings
from django.db import transaction
from kombu.utils.uuid import uuid as celery_uuid

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .compare_escalations import compare_escalations
from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=0 if settings.DEBUG else None
)
def escalate_alert_group(alert_group_pk):
    """
    This task is on duty to send escalated alerts and schedule further escalation.
    """
    from apps.alerts.models import AlertGroup

    task_logger.debug(f"Start escalate_alert_group for alert_group {alert_group_pk}")

    log_message = ""

    with transaction.atomic():
        try:
            alert_group = AlertGroup.objects.filter(pk=alert_group_pk).select_for_update()[0]  # Lock alert_group:
        except IndexError:
            return f"Alert group with pk {alert_group_pk} doesn't exist"

        if not compare_escalations(escalate_alert_group.request.id, alert_group.active_escalation_id):
            return "Active escalation ID mismatch. Duplication or non-active escalation triggered. Active: {}".format(
                alert_group.active_escalation_id
            )

        if alert_group.resolved or alert_group.acknowledged or alert_group.is_silenced_forever:
            task_logger.info(f"alert_group {alert_group.pk} resolved, acked or silenced forever. No need to escalate.")
            alert_group.stop_escalation()
            return

        if alert_group.is_silenced_for_period:
            # escalation will be restarted by unsilence_task
            task_logger.info(
                f"alert_group {alert_group.pk} silenced for period. Escalation will be restarted by unsilence_task"
            )
            return

        if alert_group.root_alert_group is not None:
            # TODO: consistent_is_escalation_finished remove this check for is_escalation_finished
            return "Alert is dependent on another. No need to activate escalation."

        if alert_group.wiped_at is not None:
            # TODO: consistent_is_escalation_finished remove this check for is_escalation_finished
            return "Alert is wiped. No need to activate escalation."

        escalation_snapshot = alert_group.escalation_snapshot

        if escalation_snapshot is None:
            return (
                f"alert_group {alert_group_pk} has no saved escalation snapshot. "
                f"Probably its channel filter was deleted or has no attached escalation chain."
            )

        escalation_snapshot.execute_actual_escalation_step()

        alert_group.raw_escalation_snapshot = escalation_snapshot.convert_to_dict()

        if escalation_snapshot.stop_escalation:
            alert_group.is_escalation_finished = True
            alert_group.save(update_fields=["is_escalation_finished", "raw_escalation_snapshot"])
            log_message += "Alert lifecycle finished. OnCall will be silent about this incident from now. "
        elif escalation_snapshot.pause_escalation:
            alert_group.save(update_fields=["raw_escalation_snapshot"])
            log_message += "Escalation is paused. "
        else:
            eta = escalation_snapshot.next_step_eta

            task_id = celery_uuid()
            alert_group.active_escalation_id = task_id
            transaction.on_commit(
                lambda: escalate_alert_group.apply_async((alert_group.pk,), immutable=True, eta=eta, task_id=task_id)
            )
            alert_group.save(update_fields=["active_escalation_id", "raw_escalation_snapshot"])
            log_message += "Next escalation poked, id: {} ".format(task_id)

        task_logger.debug(f"end of transaction in escalate_alert_group for alert_group {alert_group_pk}")
    task_logger.debug(f"Finish escalate_alert_group for alert_group {alert_group_pk}")
    return log_message + "Escalation executed."
