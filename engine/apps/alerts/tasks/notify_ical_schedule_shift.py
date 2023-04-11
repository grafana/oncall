import datetime
import json
from copy import copy

import icalendar
from django.apps import apps
from django.utils import timezone

from apps.schedules.ical_events import ical_events
from apps.schedules.ical_utils import (
    calculate_shift_diff,
    event_start_end_all_day_with_respect_to_type,
    get_icalendar_tz_or_utc,
    get_usernames_from_ical_event,
    is_icals_equal,
    memoized_users_in_ical,
)
from apps.slack.scenarios import scenario_step
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger


def get_current_shifts_from_ical(calendar, schedule, min_priority=0):
    calendar_tz = get_icalendar_tz_or_utc(calendar)
    now = timezone.datetime.now(timezone.utc)
    events_from_ical_for_three_days = ical_events.get_events_from_ical_between(
        calendar, now - timezone.timedelta(days=1), now + timezone.timedelta(days=1)
    )
    shifts = {}
    current_users = {}
    for event in events_from_ical_for_three_days:
        usernames, priority = get_usernames_from_ical_event(event)
        users = memoized_users_in_ical(tuple(usernames), schedule.organization)
        if len(users) > 0:
            event_start, event_end, all_day_event = event_start_end_all_day_with_respect_to_type(event, calendar_tz)

            if event["UID"] in shifts:
                existing_event = shifts[event["UID"]]
                if existing_event["start"] < now < existing_event["end"]:
                    continue
            shifts[event["UID"]] = {
                "users": [u.pk for u in users],
                "start": event_start,
                "end": event_end,
                "all_day": all_day_event,
                "priority": priority + min_priority,  # increase priority for overrides
                "priority_increased_by": min_priority,
            }
            current_users[event["UID"]] = users

    return shifts, current_users


def get_next_shifts_from_ical(calendar, schedule, min_priority=0, days_to_lookup=3):
    calendar_tz = get_icalendar_tz_or_utc(calendar)
    now = timezone.datetime.now(timezone.utc)
    next_events_from_ical = ical_events.get_events_from_ical_between(
        calendar, now - timezone.timedelta(days=1), now + timezone.timedelta(days=days_to_lookup)
    )
    shifts = {}
    for event in next_events_from_ical:
        usernames, priority = get_usernames_from_ical_event(event)
        users = memoized_users_in_ical(tuple(usernames), schedule.organization)
        if len(users) > 0:
            event_start, event_end, all_day_event = event_start_end_all_day_with_respect_to_type(event, calendar_tz)

            # next_shifts are not stored in db so we can use User objects directly
            shifts[f"{event_start.timestamp()}_{event['UID']}"] = {
                "users": users,
                "start": event_start,
                "end": event_end,
                "all_day": all_day_event,
                "priority": priority + min_priority,  # increase priority for overrides
                "priority_increased_by": min_priority,
            }

    return shifts


def recalculate_shifts_with_respect_to_priority(shifts, users=None):
    flag = True
    while flag:
        splitted_shifts = {}
        uids_to_pop = set()
        splitted = False
        flag = False
        for outer_k, outer_shift in shifts.items():
            if not splitted:
                for inner_k, inner_shift in shifts.items():
                    if outer_k == inner_k:
                        continue
                    else:
                        if outer_shift.get("priority", 0) > inner_shift.get("priority", 0):
                            if outer_shift["start"] > inner_shift["start"] and outer_shift["end"] < inner_shift["end"]:
                                new_uid_r = f"{inner_k}-split-r"
                                new_uid_l = f"{inner_k}-split-l"
                                splitted_shift_left = copy(inner_shift)
                                splitted_shift_right = copy(inner_shift)
                                splitted_shift_left["end"] = outer_shift["start"]
                                splitted_shift_right["start"] = outer_shift["end"]
                                splitted_shift_left["all_day"] = False
                                splitted_shift_right["all_day"] = False
                                splitted_shifts[new_uid_l] = splitted_shift_left
                                splitted_shifts[new_uid_r] = splitted_shift_right
                                uids_to_pop.add(inner_k)
                                if users is not None:
                                    users[new_uid_l] = users[inner_k]
                                    users[new_uid_r] = users[inner_k]

                                splitted = True
                                flag = True
                                break
                            elif outer_shift["start"] <= inner_shift["start"] < outer_shift["end"] < inner_shift["end"]:
                                inner_shift["start"] = outer_shift["end"]
                                flag = True
                            elif outer_shift["end"] >= inner_shift["end"] > outer_shift["start"] > inner_shift["start"]:
                                inner_shift["end"] = outer_shift["start"]
                                flag = True
                            elif (
                                outer_shift["start"] <= inner_shift["start"]
                                and outer_shift["end"] >= inner_shift["end"]
                            ):
                                uids_to_pop.add(inner_k)
                                flag = True
                            else:
                                flag = False
                        elif outer_shift.get("priority", 0) < inner_shift.get("priority", 0):
                            if inner_shift["start"] > outer_shift["start"] and inner_shift["end"] < outer_shift["end"]:
                                new_uid_r = f"{outer_k}-split-r"
                                new_uid_l = f"{outer_k}-split-l"
                                splitted_shift_left = copy(outer_shift)
                                splitted_shift_right = copy(outer_shift)
                                splitted_shift_left["all_day"] = False
                                splitted_shift_right["all_day"] = False
                                splitted_shift_left["end"] = inner_shift["start"]
                                splitted_shift_right["start"] = inner_shift["end"]
                                splitted_shifts[new_uid_l] = splitted_shift_left
                                splitted_shifts[new_uid_r] = splitted_shift_right
                                uids_to_pop.add(outer_k)

                                if users is not None:
                                    users[new_uid_l] = users[outer_k]
                                    users[new_uid_r] = users[outer_k]

                                splitted = True
                                flag = True
                                break
                            elif inner_shift["start"] <= outer_shift["start"] < inner_shift["end"] < outer_shift["end"]:
                                outer_shift["start"] = inner_shift["end"]
                                flag = True
                            elif inner_shift["end"] >= outer_shift["end"] > inner_shift["start"] > outer_shift["start"]:
                                outer_shift["end"] = inner_shift["start"]
                                flag = True
                            elif (
                                inner_shift["start"] <= outer_shift["start"]
                                and inner_shift["end"] >= outer_shift["end"]
                            ):
                                uids_to_pop.add(outer_k)
                                flag = True
                            else:
                                flag = False
                        else:
                            flag = False
            else:
                break

        shifts.update(splitted_shifts)
        for uid in uids_to_pop:
            shifts.pop(uid)


@shared_dedicated_queue_retry_task()
def notify_ical_schedule_shift(schedule_pk):
    task_logger.info(f"Notify ical schedule shift {schedule_pk}")
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    try:
        schedule = OnCallSchedule.objects.get(
            pk=schedule_pk, cached_ical_file_primary__isnull=False, channel__isnull=False
        )
    except OnCallSchedule.DoesNotExist:
        task_logger.info(f"Trying to notify ical schedule shift for non-existing schedule {schedule_pk}")
        return

    if schedule.organization.slack_team_identity is None:
        task_logger.info(f"Trying to notify ical schedule shift with no slack team identity {schedule_pk}")
        return

    MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT = 3

    ical_changed = False

    now = timezone.datetime.now(timezone.utc)
    # get list of iCalendars from current iCal files. If there is more than one calendar, primary calendar will always
    # be the first
    current_calendars = schedule.get_icalendars()

    current_shifts = {}
    # expected current_shifts structure:
    # {
    #   some uid: {
    #       "users": [users pks],
    #       "start": event start date,
    #       "end": event end date,
    #       "all_day": bool if event has all-day type,
    #       "priority": priority level,
    #       "priority_increased_by": min priority level of primary calendar,  (for primary calendar event it is 0)
    #   },
    # }

    # Current_user dict exists because it's bad idea to serialize User objects.
    # Instead users' pks are stored in db for calculation related to shift diff.
    # When it is needed to pass shift's user (e.g. in def get_report_blocks_ical())
    # we take users from current_users{} by shift uuid and replace users' pk
    current_users = {}

    overrides_priority = 0
    for calendar in current_calendars:
        if calendar is not None:
            current_shifts_result, current_users_result = get_current_shifts_from_ical(
                calendar,
                schedule,
                overrides_priority,
            )
            if overrides_priority == 0 and current_shifts_result:
                overrides_priority = max([current_shifts_result[uid]["priority"] for uid in current_shifts_result]) + 1
            current_shifts.update(current_shifts_result)
            current_users.update(current_users_result)

    recalculate_shifts_with_respect_to_priority(current_shifts, current_users)

    # drop events that don't intersection with current time
    drop = []
    for uid, current_shift in current_shifts.items():
        if not current_shift["start"] < now < current_shift["end"]:
            drop.append(uid)
    for item in drop:
        current_shifts.pop(item)

    is_prev_ical_diff = False
    prev_overrides_priority = 0
    prev_shifts = {}
    prev_users = {}

    # Get list of tuples with prev and current ical file for each calendar. If there is more than one calendar, primary
    # calendar will be the first.
    # example result for ical calendar:
    # [(prev_ical_file_primary, current_ical_file_primary), (prev_ical_file_overrides, current_ical_file_overrides)]
    # example result for calendar with custom events:
    # [(prev_ical_file, current_ical_file)]
    prev_and_current_ical_files = schedule.get_prev_and_current_ical_files()

    for prev_ical_file, current_ical_file in prev_and_current_ical_files:
        if prev_ical_file and (not current_ical_file or not is_icals_equal(current_ical_file, prev_ical_file)):
            # If icals are not equal then compare current_events from them
            is_prev_ical_diff = True
            prev_calendar = icalendar.Calendar.from_ical(prev_ical_file)

            prev_shifts_result, prev_users_result = get_current_shifts_from_ical(
                prev_calendar,
                schedule,
                prev_overrides_priority,
            )
            if prev_overrides_priority == 0 and prev_shifts_result:
                prev_overrides_priority = max([prev_shifts_result[uid]["priority"] for uid in prev_shifts_result]) + 1

            prev_shifts.update(prev_shifts_result)
            prev_users.update(prev_users_result)

    recalculate_shifts_with_respect_to_priority(prev_shifts, prev_users)

    if is_prev_ical_diff:
        # drop events that don't intersection with current time
        drop = []
        for uid, prev_shift in prev_shifts.items():
            if not prev_shift["start"] < now < prev_shift["end"]:
                drop.append(uid)
        for item in drop:
            prev_shifts.pop(item)

        shift_changed, diff_uids = calculate_shift_diff(current_shifts, prev_shifts)

    else:
        # Else comparing events from prev and current shifts
        prev_shifts = json.loads(schedule.current_shifts) if not schedule.empty_oncall else {}
        # convert datetimes which was dumped to str back to datetime to calculate shift diff correct
        str_format = "%Y-%m-%d %X%z"
        for prev_shift in prev_shifts.values():
            prev_shift["start"] = datetime.datetime.strptime(prev_shift["start"], str_format)
            prev_shift["end"] = datetime.datetime.strptime(prev_shift["end"], str_format)

        shift_changed, diff_uids = calculate_shift_diff(current_shifts, prev_shifts)

    if shift_changed:
        # Get only new/changed shifts to send a reminder message.
        new_shifts = []
        for uid in diff_uids:
            # using copy to not to mutate original current_shifts dict which will be stored in db as current_shifts
            new_shift = copy(current_shifts[uid])
            # replace users' pk by objects to make reminder message from new shifts
            new_shift["users"] = current_users[uid]
            new_shifts.append(new_shift)
        new_shifts = sorted(new_shifts, key=lambda shift: shift["start"])

        if len(new_shifts) != 0:
            days_to_lookup = (new_shifts[-1]["end"].date() - now.date()).days + 1
            days_to_lookup = max([days_to_lookup, MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT])
        else:
            days_to_lookup = MIN_DAYS_TO_LOOKUP_FOR_THE_END_OF_EVENT

        next_shifts = {}
        next_overrides_priority = 0

        for calendar in current_calendars:
            if calendar is not None:
                next_shifts_result = get_next_shifts_from_ical(
                    calendar,
                    schedule,
                    next_overrides_priority,
                    days_to_lookup=days_to_lookup,
                )
                if next_overrides_priority == 0 and next_shifts_result:
                    next_overrides_priority = (
                        max([next_shifts_result[uid]["priority"] for uid in next_shifts_result]) + 1
                    )

                next_shifts.update(next_shifts_result)

        recalculate_shifts_with_respect_to_priority(next_shifts)

        # drop events that already started
        drop = []
        for uid, next_shift in next_shifts.items():
            if now > next_shift["start"]:
                drop.append(uid)
        for item in drop:
            next_shifts.pop(item)

        next_shifts_from_ical = sorted(next_shifts.values(), key=lambda shift: shift["start"])

        upcoming_shifts = []
        # Add the earliest next_shift
        if len(next_shifts_from_ical) > 0:
            earliest_shift = next_shifts_from_ical[0]
            upcoming_shifts.append(earliest_shift)
            # Check if there are next shifts with the same start as the earliest
            for shift in next_shifts_from_ical[1:]:
                if shift["start"] == earliest_shift["start"]:
                    upcoming_shifts.append(shift)

        empty_oncall = len(current_shifts) == 0
        if empty_oncall:
            schedule.empty_oncall = True
        else:
            schedule.empty_oncall = False
            schedule.current_shifts = json.dumps(current_shifts, default=str)

        schedule.save(update_fields=["current_shifts", "empty_oncall"])

        if len(new_shifts) > 0 or empty_oncall:
            slack_client = SlackClientWithErrorHandling(schedule.organization.slack_team_identity.bot_access_token)
            step = scenario_step.ScenarioStep.get_step("schedules", "EditScheduleShiftNotifyStep")
            report_blocks = step.get_report_blocks_ical(new_shifts, upcoming_shifts, schedule, empty_oncall)

            if schedule.notify_oncall_shift_freq != OnCallSchedule.NotifyOnCallShiftFreq.NEVER:
                try:
                    if ical_changed:
                        slack_client.api_call(
                            "chat.postMessage", channel=schedule.channel, text=f"Schedule {schedule.name} was changed"
                        )

                    slack_client.api_call(
                        "chat.postMessage",
                        channel=schedule.channel,
                        blocks=report_blocks,
                        text=f"On-call shift for schedule {schedule.name} has changed",
                    )
                except SlackAPITokenException:
                    pass
                except SlackAPIException as e:
                    if e.response["error"] == "channel_not_found":
                        print(e)
                    elif e.response["error"] == "is_archived":
                        print(e)
                    elif e.response["error"] == "invalid_auth":
                        print(e)
                    else:
                        raise e
