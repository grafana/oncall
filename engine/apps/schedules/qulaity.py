# todo: add tests

import datetime
from dataclasses import dataclass
from typing import Union

import pytz

from apps.user_management.models import User


def get_day_start(dt: Union[datetime.datetime, datetime.date]) -> datetime.datetime:
    return datetime.datetime.combine(dt, datetime.datetime.min.time(), tzinfo=pytz.UTC)


def get_day_end(dt: Union[datetime.datetime, datetime.date]) -> datetime.datetime:
    return datetime.datetime.combine(dt, datetime.datetime.max.time(), tzinfo=pytz.UTC)


def event_duration(event: dict) -> datetime.timedelta:
    start = event["start"]
    end = event["end"]

    if event["all_day"]:
        start = get_day_start(start)
        end = get_day_end(end)

    return end - start


@dataclass
class Day:
    weekday: str
    start: datetime.datetime
    end: datetime.datetime


def split_to_days(start: datetime.datetime, end: datetime.datetime) -> list[Day]:
    days = []
    current_start = start

    while True:
        current_day_end = get_day_end(current_start)
        current_end = min(current_day_end, end)

        day_name = current_start.strftime("%A").lower()
        days.append(Day(day_name, current_start, current_end))

        if end <= current_day_end:
            break

        current_start = get_day_start(current_end + datetime.timedelta(days=1))

    return days


def working_hours_to_time(value):
    hours, minutes, _ = map(int, value.split(":"))
    return datetime.time(hours, minutes)


def event_duration_inside_working_hours(event: dict, working_hours: dict) -> datetime.timedelta:
    event_start = event["start"]
    event_end = event["end"]

    if event["all_day"]:
        event_start = get_day_start(event_start)
        event_end = get_day_end(event_end)

    days = split_to_days(event_start, event_end)
    result = datetime.timedelta(seconds=0)

    for day in days:
        working_hours_start = working_hours_to_time(working_hours[day.weekday][0]["start"])
        working_hours_end = working_hours_to_time(working_hours[day.weekday][0]["end"])

        work_start = datetime.datetime.combine(
            day.start,
            working_hours_start,
            tzinfo=pytz.UTC,
        )

        work_end = datetime.datetime.combine(
            day.end,
            working_hours_end,
            tzinfo=pytz.UTC,
        )

        # todo: check this

        if (day.start < work_start and day.end < work_start) or (day.start > work_end and day.end > work_end):
            continue

        if work_start <= day.start <= work_end and work_start <= day.end <= work_end:
            result += day.end - day.start

        if day.start < work_start and day.end > work_end:
            result += work_end - work_start

        if day.start >= work_start:
            result += work_end - day.start
        else:
            result += day.end - work_start

    return result


def get_event_score(events, days):
    duration = sum((event_duration(event) for event in events), start=datetime.timedelta(seconds=0))
    score = min(duration / datetime.timedelta(days=days), 1)  # todo: deal with overlapping events
    return score


def get_inside_working_hours_score(events):
    inside_working_hours_duration = datetime.timedelta(seconds=0)
    for event in events:
        users = event["users"]

        for user in users:
            u = User.objects.get(public_primary_key=user["pk"])  # todo: fetch users all at once
            inside_working_hours_duration += event_duration_inside_working_hours(event, u.working_hours)

    events_duration = sum((event_duration(event) for event in events), start=datetime.timedelta(seconds=0))
    score = inside_working_hours_duration / events_duration

    return score


def get_schedule_score(events, days):
    good_events = [
        event for event in events if not event["is_override"] and not event["is_gap"] and not event["is_empty"]
    ]

    good_event_score = get_event_score(good_events, days)
    inside_working_hours_score = get_inside_working_hours_score(good_events)

    return {
        "good_event_score": good_event_score,
        "inside_working_hours_score": inside_working_hours_score,
    }


# todo: add balance and outside working hours balance

#     good_events = [
#         event for event in events if not event["is_override"] and not event["is_gap"] and not event["is_empty"]
#     ]
#     good_events_duration = sum(event_duration(event) for event in good_events)
#     good_event_score = min(good_events_duration / (days * 24 * 60 * 60), 1)  # todo: deal with overlapping events
#
#
#     users_to_events_map = {}
#     for event in good_events:
#         users = event["users"]
#
#         for user in users:
#             user_pk = user["pk"]
#             if user_pk in users_to_events_map:
#                 users_to_events_map[user_pk].append(event)
#             else:
#                 users_to_events_map[user_pk] = [event]
#
#     res = {}
#     for user, events in users_to_events_map.items():
#         seconds = sum(event_duration(event) for event in events)
#         res[user] = seconds
#
#     score = 0
#     number_of_pairs = 0
#     for user_1 in res.keys():
#         for user_2 in res.keys():
#             if user_1 == user_2:
#                 continue
#             score += min(res[user_1], res[user_2]) / max(res[user_1], res[user_2])
#             number_of_pairs += 1
#
#     if number_of_pairs == 0:
#         balance_score = 1
#     else:
#         balance_score = score / number_of_pairs
#
#     total = 0.5 * balance_score + 0.5 * good_event_score
