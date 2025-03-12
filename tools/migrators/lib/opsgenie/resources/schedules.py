from datetime import datetime, timedelta
from typing import Dict, List, Optional

from lib.oncall.api_client import OnCallAPIClient
from lib.utils import dt_to_oncall_datetime


def match_schedule(
    schedule: dict, oncall_schedules: List[dict], user_id_map: Dict[str, str]
) -> None:
    """Match OpsGenie schedule with Grafana OnCall schedule."""
    oncall_schedule = None
    for candidate in oncall_schedules:
        if schedule["name"].lower().strip() == candidate["name"].lower().strip():
            oncall_schedule = candidate

    schedule["migration_errors"] = []
    schedule["oncall_schedule"] = oncall_schedule


def migrate_schedule(schedule: dict, user_id_map: Dict[str, str]) -> None:
    """Migrate OpsGenie schedule to Grafana OnCall."""
    if schedule["oncall_schedule"]:
        OnCallAPIClient.delete(f"schedules/{schedule['oncall_schedule']['id']}")

    # Create new schedule
    payload = {
        "name": schedule["name"],
        "type": "web",
        "team_id": None,
        "time_zone": schedule["timezone"],
    }
    oncall_schedule = OnCallAPIClient.create("schedules", payload)
    schedule["oncall_schedule"] = oncall_schedule

    # Migrate rotations
    for rotation in schedule["rotations"]:
        if not rotation["enabled"]:
            continue

        # Convert OpsGenie rotation type to OnCall frequency and interval
        frequency, interval = _convert_rotation_type(rotation["type"], rotation["length"])

        # Get start and end dates
        start_date = datetime.fromisoformat(rotation["startDate"].replace("Z", "+00:00"))
        end_date = None
        if rotation.get("endDate"):
            end_date = datetime.fromisoformat(rotation["endDate"].replace("Z", "+00:00"))

        # Create rotation
        rotation_payload = {
            "schedule_id": oncall_schedule["id"],
            "name": rotation["name"],
            "start": dt_to_oncall_datetime(start_date),
            "duration": interval,
            "frequency": frequency,
            "by_day": _convert_time_restriction(rotation.get("timeRestriction", {})),
            "users": [
                user_id_map[p["id"]]
                for p in rotation["participants"]
                if p["type"] == "user" and p["id"] in user_id_map
            ],
        }

        if end_date:
            rotation_payload["until"] = dt_to_oncall_datetime(end_date)

        OnCallAPIClient.create("rotations", rotation_payload)


def _convert_rotation_type(rotation_type: str, length: int) -> tuple[str, int]:
    """Convert OpsGenie rotation type to OnCall frequency and interval."""
    if rotation_type == "daily":
        return "daily", length * 24 * 60 * 60  # Convert days to seconds
    elif rotation_type == "weekly":
        return "weekly", length * 7 * 24 * 60 * 60  # Convert weeks to seconds
    elif rotation_type == "hourly":
        return "hourly", length * 60 * 60  # Convert hours to seconds
    else:
        return "custom", length * 24 * 60 * 60  # Default to daily


def _convert_time_restriction(restriction: dict) -> Optional[List[str]]:
    """Convert OpsGenie time restriction to OnCall by_day format."""
    if not restriction or restriction.get("type") != "weekday-and-time-of-day":
        return None

    days = []
    for r in restriction.get("restrictions", []):
        start_day = r["startDay"].upper()
        end_day = r["endDay"].upper()

        # Get all days between start and end
        current = start_day
        while True:
            days.append(current[:2])  # OnCall uses 2-letter day codes
            if current == end_day:
                break
            # Move to next day
            weekdays = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
            idx = (weekdays.index(current) + 1) % 7
            current = weekdays[idx]

    return sorted(list(set(days)))
