import datetime
import itertools
from collections import defaultdict
from typing import Iterable, Union

import pytz


# TODO: add "inside working hours score" and "balance outside working hours score" when working hours editor is implemented
def get_schedule_quality_score(events: list[dict], days: int) -> dict:
    # an event is “good” if it's a primary event, not a gap and not empty
    good_events = [
        event for event in events if not event["is_override"] and not event["is_gap"] and not event["is_empty"]
    ]
    good_event_score = get_good_event_score(good_events, days)

    # formula for balance score is taken from here: https://github.com/grafana/oncall/issues/118
    balance_score, overloaded_users = get_balance_score(good_events)

    if events:
        total_score = (good_event_score + balance_score) / 2
    else:
        total_score = 0

    info_comments = []
    warning_comments = []

    if good_event_score < 1:
        warning_comments.append("Schedule has gaps")
    else:
        info_comments.append("Schedule has no gaps")

    if balance_score < 0.8:
        warning_comments.append("Schedule has balance issues")
    elif 0.8 <= balance_score < 1:
        info_comments.append("Schedule is well-balanced, but still can be improved")
    else:
        info_comments.append("Schedule is perfectly balanced")

    comments = [{"type": "warning", "text": comment} for comment in warning_comments]
    comments += [{"type": "info", "text": comment} for comment in info_comments]

    return {
        "total_score": score_to_percent(total_score),
        "comments": comments,
        "overloaded_users": overloaded_users,
    }


def get_good_event_score(good_events: list[dict], days: int) -> float:
    good_events_duration = timedelta_sum(event_duration(event) for event in good_events)
    good_event_score = min(
        good_events_duration / datetime.timedelta(days=days), 1
    )  # todo: deal with overlapping events

    return good_event_score


def get_balance_score(events: list[dict]) -> tuple[float, list[str]]:
    duration_map = defaultdict(datetime.timedelta)
    for event in events:
        for user in event["users"]:
            user_pk = user["pk"]
            duration_map[user_pk] += event_duration(event)

    if len(duration_map) == 0:
        return 1, []

    average_duration = timedelta_sum(duration_map.values()) / len(duration_map)
    overloaded_users = [user_pk for user_pk, duration in duration_map.items() if duration > average_duration]

    return get_balance_score_by_duration_map(duration_map), overloaded_users


def get_balance_score_by_duration_map(duration_map: dict[str, datetime.timedelta]) -> float:
    if len(duration_map) <= 1:
        return 1

    score = 0
    for key_1, key_2 in itertools.combinations(duration_map, 2):
        duration_1 = duration_map[key_1]
        duration_2 = duration_map[key_2]

        score += min(duration_1, duration_2) / max(duration_1, duration_2)

    number_of_pairs = len(duration_map) * (len(duration_map) - 1) // 2
    balance_score = score / number_of_pairs
    return balance_score


def get_day_start(dt: Union[datetime.datetime, datetime.date]) -> datetime.datetime:
    return datetime.datetime.combine(dt, datetime.datetime.min.time(), tzinfo=pytz.UTC)


def get_day_end(dt: Union[datetime.datetime, datetime.date]) -> datetime.datetime:
    return datetime.datetime.combine(dt, datetime.datetime.max.time(), tzinfo=pytz.UTC)


def event_duration(event: dict) -> datetime.timedelta:
    start = event["start"]
    end = event["end"]

    if event["all_day"]:
        start = get_day_start(start)
        # adding one microsecond to the end datetime to make sure 1 day-long events are really 1 day long
        end = get_day_end(end) + datetime.timedelta(microseconds=1)

    return end - start


def timedelta_sum(deltas: Iterable[datetime.timedelta]) -> datetime.timedelta:
    return sum(deltas, start=datetime.timedelta())


def score_to_percent(score: float) -> int:
    return round(score * 100)
