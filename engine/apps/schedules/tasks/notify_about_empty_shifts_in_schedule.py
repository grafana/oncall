import pytz
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from apps.slack.utils import format_datetime_to_slack_with_time, post_message_to_channel
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import trim_if_needed

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def start_notify_about_empty_shifts_in_schedule():
    from apps.schedules.models import OnCallSchedule

    task_logger.info("Start start_notify_about_empty_shifts_in_schedule")

    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)
    schedules = OnCallSchedule.objects.filter(
        Q(empty_shifts_report_sent_at__lte=week_ago) | Q(empty_shifts_report_sent_at__isnull=True),
        slack_channel__isnull=False,
        organization__deleted_at__isnull=True,
    )

    for schedule in schedules:
        notify_about_empty_shifts_in_schedule_task.apply_async((schedule.pk,))

    task_logger.info("Finish start_notify_about_empty_shifts_in_schedule")


@shared_dedicated_queue_retry_task()
def notify_about_empty_shifts_in_schedule_task(schedule_pk):
    from apps.schedules.models import OnCallSchedule

    task_logger.info(f"Start notify_about_empty_shifts_in_schedule_task {schedule_pk}")

    cache_key = get_cache_key_notify_about_empty_shifts_in_schedule(schedule_pk)
    cached_task_id = cache.get(cache_key)
    current_task_id = notify_about_empty_shifts_in_schedule_task.request.id
    if current_task_id != cached_task_id and cached_task_id is not None:
        return
    try:
        schedule = OnCallSchedule.objects.get(pk=schedule_pk, slack_channel__isnull=False)
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to notify_about_empty_shifts_in_schedule_task for non-existing schedule {schedule_pk}")
        return

    empty_shifts = schedule.get_empty_shifts_for_next_days()
    schedule.empty_shifts_report_sent_at = timezone.now().date()

    if len(empty_shifts) != 0:
        schedule.has_empty_shifts = True
        text = (
            f"Reviewing *{schedule.slack_url}* on-call schedule found events without valid associated users.\n"
            f"To ensure you don't miss any notifications, make sure user exists (or you provided a valid Grafana username). "
            f"The user should have the right permissions, or be an Editor or Admin.\n\n"
        )
        for idx, empty_shift in enumerate(empty_shifts):
            start_timestamp = empty_shift.start.astimezone(pytz.UTC).timestamp()
            end_timestamp = empty_shift.end.astimezone(pytz.UTC).timestamp()

            if empty_shift.summary:
                text += f"*Title*: {trim_if_needed(empty_shift.summary)}\n"
            if empty_shift.description:
                text += f"*Description*: {trim_if_needed(empty_shift.description)}\n"
            if empty_shift.attendee:
                text += f"*Parsed from PagerDuty*: {trim_if_needed(empty_shift.attendee)}\n"

            if empty_shift.all_day:
                if empty_shift.start.day == empty_shift.end.day:
                    all_day_text = f'{empty_shift.start.strftime("%b %d")}\n'
                else:
                    all_day_text = (
                        f'From {empty_shift.start.strftime("%b %d")} to {empty_shift.end.strftime("%b %d")}\n'
                    )
                text += all_day_text
                text += '*All-day* event in "UTC" TZ\n'
            else:
                text += f"From {format_datetime_to_slack_with_time(start_timestamp)} to {format_datetime_to_slack_with_time(end_timestamp)} (your TZ)\n"
            if idx != len(empty_shifts) - 1:
                text += "\n\n"
        post_message_to_channel(schedule.organization, schedule.slack_channel_slack_id, text)
    else:
        schedule.has_empty_shifts = False
    schedule.save(update_fields=["empty_shifts_report_sent_at", "has_empty_shifts"])
    task_logger.info(f"Finish notify_about_empty_shifts_in_schedule_task {schedule_pk}")


def get_cache_key_notify_about_empty_shifts_in_schedule(schedule_pk):
    CACHE_KEY_PREFIX = "notify_about_empty_shifts_in_schedule"
    return f"{CACHE_KEY_PREFIX}_{schedule_pk}"


@shared_dedicated_queue_retry_task
def schedule_notify_about_empty_shifts_in_schedule(schedule_pk):
    CACHE_LIFETIME = 600
    START_TASK_DELAY = 60
    task = notify_about_empty_shifts_in_schedule_task.apply_async(args=[schedule_pk], countdown=START_TASK_DELAY)
    cache_key = get_cache_key_notify_about_empty_shifts_in_schedule(schedule_pk)
    cache.set(cache_key, task.id, timeout=CACHE_LIFETIME)
