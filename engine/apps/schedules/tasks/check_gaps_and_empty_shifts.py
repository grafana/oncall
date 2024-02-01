from celery.utils.log import get_task_logger

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def check_gaps_and_empty_shifts_in_schedule(schedule_pk):
    from apps.schedules.models import OnCallSchedule

    task_logger.info(f"Start check_gaps_and_empty_shifts_in_schedule {schedule_pk}")

    try:
        schedule = OnCallSchedule.objects.get(
            pk=schedule_pk,
        )
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to check_gaps_and_empty_shifts_in_schedule for non-existing schedule {schedule_pk}")
        return

    schedule.check_gaps_and_empty_shifts_for_next_week()
    task_logger.info(f"Finish check_gaps_and_empty_shifts_in_schedule {schedule_pk}")
