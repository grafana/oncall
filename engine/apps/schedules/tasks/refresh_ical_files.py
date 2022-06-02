from celery.utils.log import get_task_logger
from django.apps import apps

from apps.alerts.tasks import notify_ical_schedule_shift
from apps.public_api.constants import DEMO_SCHEDULE_ID_CALENDAR, DEMO_SCHEDULE_ID_ICAL
from apps.schedules.ical_utils import is_icals_equal
from apps.schedules.tasks import notify_about_empty_shifts_in_schedule, notify_about_gaps_in_schedule
from apps.slack.tasks import start_update_slack_user_group_for_schedules
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def start_refresh_ical_files():
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    task_logger.info("Start refresh ical files")

    schedules = OnCallSchedule.objects.all().exclude(
        public_primary_key__in=(DEMO_SCHEDULE_ID_CALENDAR, DEMO_SCHEDULE_ID_ICAL)
    )
    for schedule in schedules:
        refresh_ical_file.apply_async((schedule.pk,))

    # Update Slack user groups with a delay to make sure all the schedules are refreshed
    start_update_slack_user_group_for_schedules.apply_async(countdown=30)


@shared_dedicated_queue_retry_task()
def refresh_ical_file(schedule_pk):
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    task_logger.info(f"Refresh ical files for schedule {schedule_pk}")

    try:
        schedule = OnCallSchedule.objects.get(pk=schedule_pk)
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to refresh non-existing schedule {schedule_pk}")
        return

    schedule.refresh_ical_file()
    if schedule.channel is not None:
        notify_ical_schedule_shift.apply_async((schedule.pk,))

    run_task_primary = False
    if schedule.cached_ical_file_primary is not None:
        if schedule.prev_ical_file_primary is None:
            run_task_primary = True
        else:
            run_task_primary = not is_icals_equal(schedule.cached_ical_file_primary, schedule.prev_ical_file_primary)
    run_task_overrides = False
    if schedule.cached_ical_file_overrides is not None:
        if schedule.prev_ical_file_overrides is None:
            run_task_overrides = True
        else:
            run_task_overrides = not is_icals_equal(
                schedule.cached_ical_file_overrides, schedule.prev_ical_file_overrides
            )
    run_task = run_task_primary or run_task_overrides
    if run_task:
        notify_about_empty_shifts_in_schedule.apply_async((schedule_pk,))
        notify_about_gaps_in_schedule.apply_async((schedule_pk,))
