import datetime

import pytz
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone

from apps.slack.utils import format_datetime_to_slack_with_time, post_message_to_channel
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def start_check_gaps_in_schedule():
    from apps.schedules.models import OnCallSchedule

    task_logger.info("Start start_check_gaps_in_schedule")

    schedules = OnCallSchedule.objects.all()

    for schedule in schedules:
        check_gaps_in_schedule.apply_async((schedule.pk,))

    task_logger.info("Finish start_check_gaps_in_schedule")


@shared_dedicated_queue_retry_task()
def check_gaps_in_schedule(schedule_pk):
    from apps.schedules.models import OnCallSchedule

    task_logger.info(f"Start check_gaps_in_schedule {schedule_pk}")

    try:
        schedule = OnCallSchedule.objects.get(
            pk=schedule_pk,
        )
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to check_gaps_in_schedule for non-existing schedule {schedule_pk}")
        return

    schedule.check_gaps_for_next_week()
    task_logger.info(f"Finish check_gaps_in_schedule {schedule_pk}")


@shared_dedicated_queue_retry_task()
def start_notify_about_gaps_in_schedule():
    from apps.schedules.models import OnCallSchedule

    task_logger.info("Start start_notify_about_gaps_in_schedule")

    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)
    schedules = OnCallSchedule.objects.filter(
        gaps_report_sent_at__lte=week_ago,
        channel__isnull=False,
    )

    for schedule in schedules:
        notify_about_gaps_in_schedule.apply_async((schedule.pk,))

    task_logger.info("Finish start_notify_about_gaps_in_schedule")


@shared_dedicated_queue_retry_task()
def notify_about_gaps_in_schedule(schedule_pk):
    from apps.schedules.models import OnCallSchedule

    task_logger.info(f"Start notify_about_gaps_in_schedule {schedule_pk}")

    cache_key = get_cache_key_notify_about_gaps_in_schedule(schedule_pk)
    cached_task_id = cache.get(cache_key)
    current_task_id = notify_about_gaps_in_schedule.request.id
    if current_task_id != cached_task_id and cached_task_id is not None:
        return

    try:
        schedule = OnCallSchedule.objects.get(pk=schedule_pk, channel__isnull=False)
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Tried to notify_about_gaps_in_schedule for non-existing schedule {schedule_pk}")
        return

    now = timezone.now()
    events = schedule.final_events(now, now + datetime.timedelta(days=7))
    gaps = [event for event in events if event["is_gap"] and not event["is_empty"]]
    schedule.gaps_report_sent_at = now.date()

    if len(gaps) != 0:
        schedule.has_gaps = True
        text = f"There are time periods that are unassigned in *{schedule.name}* on-call schedule.\n"
        for idx, gap in enumerate(gaps):
            if gap["start"]:
                start_verbal = format_datetime_to_slack_with_time(gap["start"].astimezone(pytz.UTC).timestamp())
            else:
                start_verbal = "..."
            if gap["end"]:
                end_verbal = format_datetime_to_slack_with_time(gap["end"].astimezone(pytz.UTC).timestamp())
            else:
                end_verbal = "..."
            text += f"From {start_verbal} to {end_verbal} (your TZ)\n"
            if idx != len(gaps) - 1:
                text += "\n\n"
        post_message_to_channel(schedule.organization, schedule.channel, text)
    else:
        schedule.has_gaps = False
    schedule.save(update_fields=["gaps_report_sent_at", "has_gaps"])
    task_logger.info(f"Finish notify_about_gaps_in_schedule {schedule_pk}")


def get_cache_key_notify_about_gaps_in_schedule(schedule_pk):
    CACHE_KEY_PREFIX = "notify_about_gaps_in_schedule"
    return f"{CACHE_KEY_PREFIX}_{schedule_pk}"


@shared_dedicated_queue_retry_task
def schedule_notify_about_gaps_in_schedule(schedule_pk):
    CACHE_LIFETIME = 600
    START_TASK_DELAY = 60
    task = notify_about_gaps_in_schedule.apply_async(args=[schedule_pk], countdown=START_TASK_DELAY)
    cache_key = get_cache_key_notify_about_gaps_in_schedule(schedule_pk)
    cache.set(cache_key, task.id, timeout=CACHE_LIFETIME)
