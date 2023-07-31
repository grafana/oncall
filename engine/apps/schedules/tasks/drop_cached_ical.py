from celery.utils.log import get_task_logger

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .refresh_ical_files import refresh_ical_final_schedule

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1)
def drop_cached_ical_task(schedule_pk):
    from apps.schedules.models import OnCallSchedule

    task_logger.info(f"Start drop_cached_ical_task for schedule {schedule_pk}")
    try:
        schedule = OnCallSchedule.objects.get(pk=schedule_pk)
        schedule.drop_cached_ical()
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to drop_cached_ical_task for non-existing schedule {schedule_pk}")
    else:
        # queue a refresh for final schedule
        refresh_ical_final_schedule.apply_async((schedule_pk,))
    task_logger.info(f"Finish drop_cached_ical_task for schedule {schedule_pk}")


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=1)
def drop_cached_ical_for_custom_events_for_organization(organization_id):
    from apps.schedules.models import OnCallScheduleCalendar

    for schedule in OnCallScheduleCalendar.objects.filter(organization_id=organization_id):
        drop_cached_ical_task.apply_async(
            (schedule.pk,),
        )
    task_logger.info(f"drop cached ica for org_id {organization_id}")
