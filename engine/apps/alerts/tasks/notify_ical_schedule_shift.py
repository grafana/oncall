import datetime
import json
import typing
from typing import TYPE_CHECKING

from django.utils import timezone

from apps.schedules.ical_utils import calculate_shift_diff, parse_event_uid
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger

if TYPE_CHECKING:
    from apps.schedules.models import OnCallSchedule


def convert_prev_shifts_to_new_format(prev_shifts: dict, schedule: "OnCallSchedule") -> list:
    new_prev_shifts = []
    user_ids = []
    users_info: typing.Dict[int, typing.Dict[str, str]] = {}
    for shift in prev_shifts.values():
        user_ids.extend(shift.get("users", []))
    prev_users = schedule.organization.users.filter(id__in=user_ids)
    for user in prev_users:
        users_info.setdefault(
            user.id,
            {
                "display_name": user.username,
                "email": user.email,
                "pk": user.public_primary_key,
                "avatar_full": user.avatar_full_url,
            },
        )
    for uid, shift in prev_shifts.items():
        shift_pk, _ = parse_event_uid(uid)
        new_prev_shifts.append(
            {
                "users": [users_info[user_pk] for user_pk in shift["users"]],
                "start": shift["start"],
                "end": shift["end"],
                "all_day": shift["all_day"],
                "priority_level": shift["priority"],
                "shift": {"pk": shift_pk},
            }
        )
    return new_prev_shifts


@shared_dedicated_queue_retry_task()
def notify_ical_schedule_shift(schedule_pk):
    task_logger.info(f"Start notify ical schedule shift {schedule_pk}")
    from apps.schedules.models import OnCallSchedule

    try:
        schedule = OnCallSchedule.objects.get(
            pk=schedule_pk, cached_ical_file_primary__isnull=False, channel__isnull=False
        )
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Trying to notify ical schedule shift for non-existing schedule {schedule_pk}")
        return

    if schedule.organization.slack_team_identity is None:
        task_logger.info(
            f"Trying to notify ical schedule shift with no slack team identity {schedule_pk}, "
            f"organization {schedule.organization_id}"
        )
        return
    elif schedule.organization.deleted_at:
        task_logger.info(
            f"Trying to notify ical schedule shift from deleted organization {schedule_pk}, "
            f"organization {schedule.organization_id}"
        )
        return

    task_logger.info(f"Notify ical schedule shift {schedule_pk}, organization {schedule.organization_id}")

    MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT = 3

    now = datetime.datetime.now(timezone.utc)

    current_shifts = schedule.final_events(now, now, with_empty=False, with_gap=False, ignore_untaken_swaps=True)

    prev_shifts = json.loads(schedule.current_shifts) if not schedule.empty_oncall else []
    prev_shifts_updated = False
    # convert prev_shifts to new events format for compatibility with the previous version of this task
    if prev_shifts and isinstance(prev_shifts, dict):
        prev_shifts = convert_prev_shifts_to_new_format(prev_shifts, schedule)
        prev_shifts_updated = True

    # convert datetimes which was dumped to str back to datetime to calculate shift diff correct
    str_format = "%Y-%m-%d %X%z"
    for prev_shift in prev_shifts:
        prev_shift["start"] = datetime.datetime.strptime(prev_shift["start"], str_format)
        prev_shift["end"] = datetime.datetime.strptime(prev_shift["end"], str_format)

    shift_changed, diff_shifts = calculate_shift_diff(current_shifts, prev_shifts)

    # Do not notify if there is no difference between current and previous shifts
    if not shift_changed:
        task_logger.info(f"No shift diff found for schedule {schedule_pk}, organization {schedule.organization_id}")
        # If prev shifts were converted to a new format, update related field in db
        if prev_shifts_updated:
            schedule.current_shifts = json.dumps(current_shifts, default=str)
            schedule.save(update_fields=["current_shifts"])
        return

    new_shifts = sorted(diff_shifts, key=lambda shift: shift["start"])

    # get days_to_lookup for next shifts
    if len(new_shifts) != 0:
        max_end_date = max([shift["end"].date() for shift in new_shifts])
        days_to_lookup = (max_end_date - now.date()).days + 1
        days_to_lookup = max([days_to_lookup, MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT])
    else:
        days_to_lookup = MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT

    datetime_end = now + datetime.timedelta(days=days_to_lookup)

    next_shifts_unfiltered = schedule.final_events(
        now, datetime_end, with_empty=False, with_gap=False, ignore_untaken_swaps=True
    )
    # drop events that already started
    next_shifts = []
    for next_shift in next_shifts_unfiltered:
        if now < next_shift["start"]:
            next_shifts.append(next_shift)

    upcoming_shifts = []
    # Add the earliest next_shift
    if len(next_shifts) > 0:
        earliest_shift = next_shifts[0]
        upcoming_shifts.append(earliest_shift)
        # Check if there are next shifts with the same start as the earliest
        for shift in next_shifts[1:]:
            if shift["start"] == earliest_shift["start"]:
                upcoming_shifts.append(shift)

    schedule.empty_oncall = len(current_shifts) == 0
    if not schedule.empty_oncall:
        schedule.current_shifts = json.dumps(current_shifts, default=str)

    schedule.save(update_fields=["current_shifts", "empty_oncall"])

    if len(new_shifts) > 0 or schedule.empty_oncall:
        task_logger.info(f"new_shifts: {new_shifts}")
        if schedule.notify_oncall_shift_freq != OnCallSchedule.NotifyOnCallShiftFreq.NEVER:
            slack_client = SlackClientWithErrorHandling(schedule.organization.slack_team_identity.bot_access_token)
            step = scenario_step.ScenarioStep.get_step("schedules", "EditScheduleShiftNotifyStep")
            report_blocks = step.get_report_blocks_ical(new_shifts, upcoming_shifts, schedule, schedule.empty_oncall)

            try:
                slack_client.api_call(
                    "chat.postMessage",
                    channel=schedule.channel,
                    blocks=report_blocks,
                    text=f"On-call shift for schedule {schedule.name} has changed",
                )
            except SlackAPITokenException:
                pass
            except SlackAPIException as e:
                expected_exceptions = ["channel_not_found", "is_archived", "invalid_auth"]
                if e.response["error"] in expected_exceptions:
                    print(e)
                else:
                    raise e
