import datetime
import random
from pprint import pprint
from typing import Optional

from migrator import oncall_api_client


def match_schedule(schedule: dict, oncall_schedules: list[dict]) -> None:
    oncall_schedule = None
    for candidate in oncall_schedules:
        if schedule["name"].lower().strip() == candidate["name"].lower().strip():
            oncall_schedule = candidate

    schedule["oncall_schedule"] = oncall_schedule


def migrate_schedule(schedule: dict, users) -> None:
    if schedule["oncall_schedule"]:
        oncall_api_client.delete(
            "schedules/{}".format(schedule["oncall_schedule"]["id"])
        )

    user_id_map = {u["id"]: u["oncall_user"]["id"] for u in users}
    shifts = migrate_shifts(schedule, user_id_map)

    pprint(schedule)

    payload = {
        "name": schedule["name"],
        "type": "web",
        "team_id": None,
        "time_zone": schedule["time_zone"],
        "shifts": [shift["id"] for shift in shifts],
    }
    oncall_schedule = oncall_api_client.create("schedules", payload)

    schedule["oncall_schedule"] = oncall_schedule


def migrate_shifts(schedule: dict, user_id_map):
    shift_payloads = transform_layers_to_shifts(
        schedule["schedule_layers"], user_id_map
    )
    shifts = []

    for payload in shift_payloads:
        pprint(payload)
        shift = oncall_api_client.create("on_call_shifts", payload)
        shifts.append(shift)

    return shifts


def transform_layers_to_shifts(layers, user_id_map):
    shifts = []
    for level, layer in enumerate(reversed(layers)):
        shifts += transform_layer(layer, level, user_id_map)
    return shifts


def transform_layer(layer: dict, level: int, user_id_map: dict[int, int]) -> list[dict]:
    assert not layer["restrictions"]  # TODO: deal with restrictions

    rotation_virtual_start = layer["rotation_virtual_start"]
    rotation_turn_length_seconds = layer["rotation_turn_length_seconds"]

    start = layer["start"]
    end = layer["end"]

    frequency, interval = seconds_to_frequency_and_interval(
        rotation_turn_length_seconds
    )

    rolling_users = []
    for user in layer["users"]:
        user_id = user["user"]["id"]
        oncall_user_id = user_id_map[user_id]
        rolling_users.append([oncall_user_id])

    payload = {
        "name": layer["name"]
        + str(random.randint(0, 100000)),  # TODO: does random number work?
        "type": "rolling_users",
        "start": transform_datetime(rotation_virtual_start),
        "duration": rotation_turn_length_seconds,
        "rotation_start": transform_datetime(start),
        "until": transform_datetime(end),
        "frequency": frequency,
        "interval": interval,
        "rolling_users": rolling_users,
        "level": level,
        "week_start": "MO",
        "start_rotation_from_user_index": 0,
        "time_zone": _pd_datetime_to_dt(rotation_virtual_start).tzname(),
    }
    return [payload]


def seconds_to_frequency_and_interval(seconds):
    assert seconds >= 3600, "Rotation must be at least 1 hour"
    hours = seconds // 3600

    if hours >= 24 and hours % 24 == 0:
        days = hours // 24
        if days >= 7 and days % 7 == 0:
            weeks = days // 7
            return "weekly", weeks
        else:
            return "daily", days
    else:
        return "hourly", hours


def transform_datetime(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    dt = _pd_datetime_to_dt(text)
    return _dt_to_oncall_datetime(dt)


def _pd_datetime_to_dt(text: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(text)


def _dt_to_oncall_datetime(dt: datetime.datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
