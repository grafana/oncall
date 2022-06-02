from time import perf_counter

from celery.utils.log import get_task_logger
from django.apps import apps
from django.db import transaction
from django.utils import timezone

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(bind=True)
def heartbeat_checkup(self, heartbeat_id):
    HeartBeat = apps.get_model("heartbeat", "HeartBeat")
    HeartBeat.perform_heartbeat_check(heartbeat_id, heartbeat_checkup.request.id)


@shared_dedicated_queue_retry_task()
def integration_heartbeat_checkup(heartbeat_id):
    IntegrationHeartBeat = apps.get_model("heartbeat", "IntegrationHeartBeat")
    IntegrationHeartBeat.perform_heartbeat_check(heartbeat_id, integration_heartbeat_checkup.request.id)


@shared_dedicated_queue_retry_task()
def restore_heartbeat_tasks():
    """
    Restore heartbeat tasks in case they got lost for some reason
    """
    HeartBeat = apps.get_model("heartbeat", "HeartBeat")
    for heartbeat in HeartBeat.objects.all():
        if (
            heartbeat.last_checkup_task_time
            + timezone.timedelta(minutes=5)
            + timezone.timedelta(seconds=heartbeat.timeout_seconds)
            < timezone.now()
        ):
            task = heartbeat_checkup.apply_async((heartbeat.pk,), countdown=5)
            heartbeat.actual_check_up_task_id = task.id
            heartbeat.save()


@shared_dedicated_queue_retry_task()
def process_heartbeat_task(alert_receive_channel_pk):
    start = perf_counter()
    IntegrationHeartBeat = apps.get_model("heartbeat", "IntegrationHeartBeat")
    with transaction.atomic():
        heartbeats = IntegrationHeartBeat.objects.filter(
            alert_receive_channel__pk=alert_receive_channel_pk,
        ).select_for_update()
        if len(heartbeats) == 0:
            logger.info(f"Integration Heartbeat for alert_receive_channel {alert_receive_channel_pk} was not found.")
            return
        else:
            heartbeat = heartbeats[0]
        heartbeat_selected = perf_counter()
        logger.info(
            f"IntegrationHeartBeat selected for alert_receive_channel {alert_receive_channel_pk} in {heartbeat_selected - start}"
        )
        task = integration_heartbeat_checkup.apply_async(
            (heartbeat.pk,),
            countdown=heartbeat.timeout_seconds + 1,
        )
        is_touched = heartbeat.last_heartbeat_time is not None
        heartbeat.actual_check_up_task_id = task.id
        heartbeat.last_heartbeat_time = timezone.now()
        update_fields = ["actual_check_up_task_id", "last_heartbeat_time"]
        task_started = perf_counter()
        logger.info(
            f"heartbeat_checkup task started for alert_receive_channel {alert_receive_channel_pk} in {task_started - start}"
        )
        if is_touched:
            state_changed = heartbeat.check_heartbeat_state()
            state_checked = perf_counter()
            logger.info(
                f"state checked for alert_receive_channel {alert_receive_channel_pk} in {state_checked - start}"
            )
            if state_changed:
                update_fields.append("previous_alerted_state_was_life")
        heartbeat.save(update_fields=update_fields)
