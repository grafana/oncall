import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from lib.constants import ONCALL_SHIFT_WEB_SOURCE
from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_FILTER_SCHEDULE_REGEX,
    OPSGENIE_FILTER_TEAM,
    OPSGENIE_FILTER_USERS,
)
from lib.utils import dt_to_oncall_datetime, duration_to_frequency_and_interval


def filter_schedules(schedules: list[dict]) -> list[dict]:
    """Apply filters to schedules."""
    if OPSGENIE_FILTER_TEAM:
        filtered_schedules = []
        for s in schedules:
            if s["ownerTeam"]["id"] == OPSGENIE_FILTER_TEAM:
                filtered_schedules.append(s)
        schedules = filtered_schedules

    if OPSGENIE_FILTER_USERS:
        filtered_schedules = []
        for schedule in schedules:
            # Check if any rotation has a participant with ID in OPSGENIE_FILTER_USERS
            include_schedule = False
            for rotation in schedule.get("rotations", []):
                for participant in rotation.get("participants", []):
                    if (
                        participant.get("type") == "user"
                        and participant.get("id") in OPSGENIE_FILTER_USERS
                    ):
                        include_schedule = True
                        break
                if include_schedule:
                    break

            # Also check overrides for the filtered users
            if not include_schedule:
                for override in schedule.get("overrides", []):
                    if (
                        override.get("user", {}).get("type") == "user"
                        and override.get("user", {}).get("id") in OPSGENIE_FILTER_USERS
                    ):
                        include_schedule = True
                        break

            if include_schedule:
                filtered_schedules.append(schedule)

        schedules = filtered_schedules

    if OPSGENIE_FILTER_SCHEDULE_REGEX:
        pattern = re.compile(OPSGENIE_FILTER_SCHEDULE_REGEX)
        schedules = [s for s in schedules if pattern.match(s["name"])]

    return schedules


def match_schedule(
    schedule: dict, oncall_schedules: List[dict], user_id_map: Dict[str, str]
) -> None:
    """
    Match OpsGenie schedule with Grafana OnCall schedule.
    """
    oncall_schedule = None
    for candidate in oncall_schedules:
        if schedule["name"].lower().strip() == candidate["name"].lower().strip():
            oncall_schedule = candidate

    # Check if any rotation has time restrictions
    has_time_restrictions = False
    for rotation in schedule.get("rotations", []):
        if rotation.get("timeRestriction"):
            has_time_restrictions = True
            break

    if has_time_restrictions:
        schedule["migration_errors"] = [
            "Schedule contains time restrictions which are not supported for migration"
        ]
        return

    _, errors = Schedule.from_dict(schedule).to_oncall_schedule(user_id_map)
    schedule["migration_errors"] = errors
    schedule["oncall_schedule"] = oncall_schedule


def match_users_for_schedule(schedule: dict, users: List[dict]) -> None:
    """
    Match users referenced in schedule.
    """
    schedule["matched_users"] = []

    for rotation in schedule["rotations"]:
        for participant in rotation["participants"]:
            if participant["type"] == "user":
                for user in users:
                    if user["id"] == participant["id"] and user.get("oncall_user"):
                        schedule["matched_users"].append(user)


def migrate_schedule(schedule: dict, user_id_map: Dict[str, str]) -> None:
    """
    Migrate OpsGenie schedule to Grafana OnCall.
    """
    if schedule["oncall_schedule"]:
        OnCallAPIClient.delete(f"schedules/{schedule['oncall_schedule']['id']}")

    schedule["oncall_schedule"] = Schedule.from_dict(schedule).migrate(user_id_map)


@dataclass
class Schedule:
    """
    Utility class for converting an OpsGenie schedule to an OnCall schedule.
    An OpsGenie schedule has multiple rotations, each with a set of participants.
    """

    name: str
    timezone: str
    rotations: list["Rotation"]
    overrides: list["Override"]

    @classmethod
    def from_dict(cls, schedule: dict) -> "Schedule":
        """Create a Schedule object from an OpsGenie API response for a schedule."""
        rotations = []
        for rotation_dict in schedule["rotations"]:
            # Skip disabled rotations
            if not rotation_dict.get("enabled", True):
                continue
            rotations.append(Rotation.from_dict(rotation_dict))

        # Process overrides
        overrides = []
        for override_dict in schedule.get("overrides", []):
            overrides.append(Override.from_dict(override_dict))

        return cls(
            name=schedule["name"],
            timezone=schedule["timezone"],
            rotations=rotations,
            overrides=overrides,
        )

    def to_oncall_schedule(
        self, user_id_map: Dict[str, str]
    ) -> tuple[Optional[dict], list[str]]:
        """
        Convert a Schedule object to an OnCall schedule.
        Note that it also returns shifts, but these are not created at the same time as the schedule.
        """
        shifts = []
        errors = []

        for rotation in self.rotations:
            # Check if all users in the rotation exist in OnCall
            missing_user_ids = [
                p["id"]
                for p in rotation.participants
                if p["type"] == "user" and p["id"] not in user_id_map
            ]
            if missing_user_ids:
                errors.append(
                    f"{rotation.name}: Users with IDs {missing_user_ids} not found in OnCall."
                )
                continue

            shifts.append(rotation.to_oncall_shift(user_id_map))

        # Process overrides
        for override in self.overrides:
            # Check if the user exists in OnCall
            if override.user_id not in user_id_map:
                errors.append(
                    f"Override: User with ID '{override.user_id}' not found in OnCall."
                )
                continue

            shifts.append(override.to_oncall_override_shift(user_id_map))

        if errors:
            return None, errors

        return {
            "name": self.name,
            "type": "web",
            "team_id": None,
            "time_zone": self.timezone,
            "shifts": shifts,
        }, []

    def migrate(self, user_id_map: Dict[str, str]) -> dict:
        """
        Create an OnCall schedule and its shifts.
        First create the shifts, then create a schedule with shift IDs provided.
        """
        schedule, errors = self.to_oncall_schedule(user_id_map)
        assert not errors, "Unexpected errors: {}".format(errors)

        # Create shifts in OnCall
        shift_ids = []
        for shift in schedule["shifts"]:
            created_shift = OnCallAPIClient.create("on_call_shifts", shift)
            shift_ids.append(created_shift["id"])

        # Create schedule in OnCall with shift IDs provided
        schedule["shifts"] = shift_ids
        new_schedule = OnCallAPIClient.create("schedules", schedule)

        return new_schedule


@dataclass
class Override:
    """
    Utility class for representing a schedule override in OpsGenie.
    """

    start_date: datetime
    end_date: datetime
    user_id: str

    @classmethod
    def from_dict(cls, override: dict) -> "Override":
        """Create an Override object from an OpsGenie API response for a schedule override."""
        # Convert string dates to datetime objects
        start_date = datetime.fromisoformat(
            override["startDate"].replace("Z", "+00:00")
        )
        end_date = datetime.fromisoformat(override["endDate"].replace("Z", "+00:00"))

        # Extract user ID from the user object
        user_id = override.get("user", {}).get("id")

        if not user_id:
            raise ValueError(f"Could not extract user ID from override: {override}")

        return cls(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )

    def to_oncall_override_shift(self, user_id_map: Dict[str, str]) -> dict:
        """Convert an Override object to an OnCall override shift."""
        duration = int((self.end_date - self.start_date).total_seconds())
        oncall_user_id = user_id_map[self.user_id]

        return {
            "name": f"Override-{uuid4().hex[:8]}",
            "type": "override",
            "team_id": None,
            "start": dt_to_oncall_datetime(self.start_date),
            "duration": duration,
            "rotation_start": dt_to_oncall_datetime(self.start_date),
            "users": [oncall_user_id],
            "time_zone": "UTC",
            "source": ONCALL_SHIFT_WEB_SOURCE,
        }


@dataclass
class Rotation:
    """
    Utility class for converting an OpsGenie rotation to an OnCall shift.
    """

    name: str
    type: str
    length: int
    start_date: datetime
    end_date: Optional[datetime]
    participants: List[dict]

    @classmethod
    def from_dict(cls, rotation: dict) -> "Rotation":
        """Create a Rotation object from an OpsGenie API response for a rotation."""
        # Keep start_date in UTC format
        start_date = datetime.fromisoformat(
            rotation["startDate"].replace("Z", "+00:00")
        )

        end_date = None
        if rotation.get("endDate"):
            end_date = datetime.fromisoformat(
                rotation["endDate"].replace("Z", "+00:00")
            )

        return cls(
            name=rotation["name"],
            type=rotation["type"],
            length=rotation["length"],
            start_date=start_date,
            end_date=end_date,
            participants=rotation["participants"],
        )

    def to_oncall_shift(self, user_id_map: Dict[str, str]) -> dict:
        """Convert a Rotation object to an OnCall shift."""
        # Calculate base duration based on type and length
        if self.type == "daily":
            base_duration = timedelta(days=self.length)
        elif self.type == "weekly":
            base_duration = timedelta(weeks=self.length)
        elif self.type == "hourly":
            base_duration = timedelta(hours=self.length)
        else:
            base_duration = timedelta(days=self.length)  # Default to daily

        # Use duration_to_frequency_and_interval to get the natural frequency
        frequency, interval = duration_to_frequency_and_interval(base_duration)

        shift = {
            "name": self.name or uuid4().hex,
            "type": "rolling_users",
            "time_zone": "UTC",
            "team_id": None,
            "level": 1,
            "start": dt_to_oncall_datetime(self.start_date),
            "duration": int(base_duration.total_seconds()),
            "frequency": frequency,
            "interval": interval,
            "rolling_users": [
                [user_id_map[p["id"]]]
                for p in self.participants
                if p["type"] == "user" and p["id"] in user_id_map
            ],
            "start_rotation_from_user_index": 0,
            "week_start": "MO",
            "source": ONCALL_SHIFT_WEB_SOURCE,
        }

        if self.end_date:
            shift["until"] = dt_to_oncall_datetime(self.end_date)

        return shift
