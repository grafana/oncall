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


def get_working_hours(user, weekday):
    if weekday in ["saturday", "sunday"]:
        return datetime.time(0, 0, 0), datetime.time(0, 0, 0)

    start = user.working_hours[weekday][0]["start"]
    end = user.working_hours[weekday][0]["end"]

    start_hour, start_minute, start_second = map(int, start.split(":"))
    end_hour, end_minute, end_second = map(int, end.split(":"))

    tzinfo = pytz.timezone(user.timezone or "UTC")

    start_result = (
        datetime.datetime.now(tz=tzinfo)
        .replace(hour=start_hour, minute=start_minute, second=start_second, microsecond=0)
        .astimezone(pytz.UTC)
        .time()
    )
    end_result = (
        datetime.datetime.now(tz=tzinfo)
        .replace(hour=end_hour, minute=end_minute, second=end_second, microsecond=0)
        .astimezone(pytz.UTC)
        .time()
    )

    return start_result, end_result


def spans_inside_working_hours(
    start: datetime.datetime,
    end: datetime.datetime,
    user: User,
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    days = split_to_days(start, end)
    result = []

    for day in days:
        working_hours_start, working_hours_end = get_working_hours(user, day.weekday)

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

        if (day.start < work_start and day.end < work_start) or (day.start > work_end and day.end > work_end):
            continue
        elif work_start <= day.start <= work_end and work_start <= day.end <= work_end:
            result.append((day.start, day.end))
        elif day.start < work_start and day.end > work_end:
            result.append((work_start, work_end))
        elif day.start >= work_start:
            result.append((day.start, work_end))
        else:
            result.append((work_start, day.end))

    return result


def get_inside_working_hours_score(events, users):
    inside_working_hours_duration = datetime.timedelta(seconds=0)

    for event in events:
        user_pks = [user["pk"] for user in event["users"]]

        for user_pk in user_pks:
            start, end = event["start"], event["end"]
            if event["all_day"]:
                start = get_day_start(start)
                end = get_day_end(end)

            user = users[user_pk]
            spans = spans_inside_working_hours(start, end, user)
            inside_working_hours_duration += timedelta_sum(span[1] - span[0] for span in spans)

    events_duration = timedelta_sum(event_duration(event) for event in events)

    if events_duration:
        score = inside_working_hours_duration / events_duration
    else:
        score = 1

    return score


def get_balance_score(events):
    users_to_events_map = {}
    for event in events:
        user_pks = [user["pk"] for user in event["users"]]

        for user_pk in user_pks:
            if user_pk in users_to_events_map:
                users_to_events_map[user_pk].append(event)
            else:
                users_to_events_map[user_pk] = [event]

    duration_map = {}
    for user_pk, events in users_to_events_map.items():
        duration_map[user_pk] = timedelta_sum(event_duration(event) for event in events)

    score = 0
    number_of_pairs = 0
    for user_1 in duration_map:
        for user_2 in duration_map:
            if user_1 == user_2:
                continue
            score += min(duration_map[user_1], duration_map[user_2]) / max(duration_map[user_1], duration_map[user_2])
            number_of_pairs += 1

    if number_of_pairs == 0:
        balance_score = 1
    else:
        balance_score = score / number_of_pairs

    return balance_score


def get_balance_outside_working_hours(events, users):
    users_to_events_map = {}
    for event in events:
        user_pks = [user["pk"] for user in event["users"]]

        for user_pk in user_pks:
            if user_pk in users_to_events_map:
                users_to_events_map[user_pk].append(event)
            else:
                users_to_events_map[user_pk] = [event]

    outside_working_hours_duration_map = {}
    for user_pk in users_to_events_map:
        outside_working_hours_duration = datetime.timedelta(seconds=0)

        for event in users_to_events_map[user_pk]:
            start, end = event["start"], event["end"]
            if event["all_day"]:
                start = get_day_start(start)
                end = get_day_end(end)

            user = users[user_pk]
            spans = spans_inside_working_hours(start, end, user)
            spans_duration = timedelta_sum(span[1] - span[0] for span in spans)
            outside_working_hours_duration += event_duration(event) - spans_duration

        outside_working_hours_duration_map[user_pk] = outside_working_hours_duration

    score = 0
    number_of_pairs = 0
    for user_1 in outside_working_hours_duration_map:
        for user_2 in outside_working_hours_duration_map:
            if user_1 == user_2:
                continue
            duration_1 = outside_working_hours_duration_map[user_1]
            duration_2 = outside_working_hours_duration_map[user_2]

            score += min(duration_1, duration_2) / max(duration_1, duration_2)
            number_of_pairs += 1

    if number_of_pairs == 0:
        balance_score = 1
    else:
        balance_score = score / number_of_pairs

    return balance_score


def timedelta_sum(x):
    return sum(x, start=datetime.timedelta(seconds=0))


def get_schedule_score(events, days):
    good_events = [
        event for event in events if not event["is_override"] and not event["is_gap"] and not event["is_empty"]
    ]

    user_pks = set()
    for event in good_events:
        for user in event["users"]:
            user_pks.add(user["pk"])
    users = {user.public_primary_key: user for user in User.objects.filter(public_primary_key__in=user_pks)}

    good_events_duration = timedelta_sum(event_duration(event) for event in good_events)
    good_event_score = min(
        good_events_duration / datetime.timedelta(days=days), 1
    )  # todo: deal with overlapping events

    inside_working_hours_score = get_inside_working_hours_score(good_events, users)

    balance_score = get_balance_score(good_events)

    balance_outside_working_hours_score = get_balance_outside_working_hours(good_events, users)

    total_score = (
        good_event_score * 0.5
        + balance_score * 0.17
        + inside_working_hours_score * 0.165
        + balance_outside_working_hours_score * 0.165
    )

    return {
        "scores": [
            {
                "id": "good_event_score",
                "title": "Good event score",
                "value": round(good_event_score * 100),
                "description": "Ratio of good events to all events",
            },
            {
                "id": "inside_working_hours_score",
                "title": "Inside working hours score",
                "value": round(inside_working_hours_score * 100),
                "description": "Ratio of time scheduled inside working hours to all time scheduled",
            },
            {
                "id": "balance_score",
                "title": "Balance score",
                "value": round(balance_score * 100),
                "description": "A score representing ...",
            },
            {
                "id": "balance_outside_working_hours_score",
                "title": "Balance outside working hours score",
                "value": round(balance_outside_working_hours_score * 100),
                "description": "A score representing ...",
            },
        ],
        "total_score": round(total_score * 100),
    }
