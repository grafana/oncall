import datetime
import enum
import itertools
from collections import defaultdict
from typing import Iterable

from apps.user_management.models import User


class CommentType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"


# TODO: add "inside working hours score" and "balance outside working hours score" when working hours editor is implemented
def get_schedule_quality_score(events: list[dict], days: int) -> dict:
    # an event is “good” if it's not a gap and not empty
    good_events = [event for event in events if not event["is_gap"] and not event["is_empty"]]
    if not good_events:
        return {
            "total_score": 0,
            "comments": [{"type": CommentType.WARNING, "text": "Schedule is empty"}],
            "overloaded_users": [],
        }

    good_event_score = get_good_event_score(good_events, days)

    # formula for balance score is taken from here: https://github.com/grafana/oncall/issues/118
    duration_map = get_duration_map(good_events)
    balance_score = get_balance_score_by_duration_map(duration_map)

    # calculate overloaded users
    if balance_score >= 0.95:  # tolerate minor imbalance
        balance_score = 1
        overloaded_users = []
    else:
        average_duration = timedelta_sum(duration_map.values()) / len(duration_map)
        overloaded_user_pks = [user_pk for user_pk, duration in duration_map.items() if duration > average_duration]
        user_map = {
            user.public_primary_key: user for user in User.objects.filter(public_primary_key__in=overloaded_user_pks)
        }
        overloaded_users = []
        for user_pk in overloaded_user_pks:
            user = user_map[user_pk]
            score = score_to_percent(duration_map[user_pk] / average_duration) - 100
            overloaded_users.append({"id": user_pk, "username": user.username, "score": score})

        # show most overloaded users first
        overloaded_users.sort(key=lambda user: user["score"], reverse=True)

    # generate comments regarding gaps
    comments = []
    if good_event_score == 1:
        comments.append({"type": CommentType.INFO, "text": "Schedule has no gaps"})
    else:
        comments.append({"type": CommentType.WARNING, "text": "Schedule has gaps"})

    # generate comments regarding balance
    if balance_score == 1:
        comments.append({"type": CommentType.INFO, "text": "Schedule is perfectly balanced"})
    else:
        comments.append({"type": CommentType.WARNING, "text": "Schedule has balance issues"})

    total_score = (good_event_score + balance_score) / 2
    return {
        "total_score": score_to_percent(total_score),
        "comments": comments,
        "overloaded_users": overloaded_users,
    }


def get_good_event_score(good_events: list[dict], days: int) -> float:
    good_events_duration = timedelta_sum(event_duration(event) for event in good_events)
    good_event_score = min(good_events_duration / datetime.timedelta(days=days), 1)

    return good_event_score


def get_duration_map(events: list[dict]) -> dict[str, datetime.timedelta]:
    duration_map = defaultdict(datetime.timedelta)
    for event in events:
        for user in event["users"]:
            user_pk = user["pk"]
            duration_map[user_pk] += event_duration(event)

    return duration_map


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


def event_duration(event: dict) -> datetime.timedelta:
    return event["end"] - event["start"]


def timedelta_sum(deltas: Iterable[datetime.timedelta]) -> datetime.timedelta:
    return sum(deltas, start=datetime.timedelta())


def score_to_percent(score: float) -> int:
    return round(score * 100)
