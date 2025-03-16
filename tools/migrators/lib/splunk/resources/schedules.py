import datetime
import typing
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from lib.constants import ONCALL_SHIFT_WEB_SOURCE
from lib.oncall import types as oncall_types
from lib.oncall.api_client import OnCallAPIClient
from lib.splunk import types
from lib.utils import dt_to_oncall_datetime, duration_to_frequency_and_interval

TIME_ZONE = "UTC"
"""
Note: The Splunk schedule rotations do return a `timezone` attribute, but I don't think
we need to worry about this as the all of the timestamps that we touch are in UTC.
"""


def generate_splunk_schedule_name(
    schedule: types.SplunkScheduleWithTeamAndRotations,
) -> str:
    return f"{schedule['policy']['name']} schedule"


def match_schedule(
    schedule: types.SplunkScheduleWithTeamAndRotations,
    oncall_schedules: list[oncall_types.OnCallSchedule],
    user_id_map: dict[str, str],
) -> None:
    schedule_name = generate_splunk_schedule_name(schedule)
    schedule["name"] = schedule_name

    oncall_schedule = None

    for candidate in oncall_schedules:
        if schedule_name.lower().strip() == candidate["name"].lower().strip():
            oncall_schedule = candidate

    _, errors = Schedule.from_dict(schedule).to_oncall_schedule(user_id_map)

    schedule["migration_errors"] = errors
    schedule["oncall_schedule"] = oncall_schedule


def migrate_schedule(
    schedule: types.SplunkScheduleWithTeamAndRotations,
    user_id_map: dict[str, str],
) -> None:
    if schedule["oncall_schedule"]:
        OnCallAPIClient.delete("schedules/{}".format(schedule["oncall_schedule"]["id"]))

    schedule["oncall_schedule"] = Schedule.from_dict(schedule).migrate(user_id_map)


def _splunk_datetime_to_dt(text: str) -> datetime.datetime:
    """
    Convert a Splunk datetime string to a datetime object.
    """
    return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Schedule:
    """
    Utility class for converting a Splunk schedule to an OnCall schedule.
    """

    name: str
    rotation_shifts: list["RotationShift"]
    overrides: list["Override"]

    @classmethod
    def from_dict(
        cls, schedule: types.SplunkScheduleWithTeamAndRotations
    ) -> "Schedule":
        """
        Create a Schedule object from a Splunk API response for a schedule.
        """
        rotation_shifts = []
        num_oncall_shift_layers = len(schedule["rotations"])

        for idx, rotation in enumerate(schedule["rotations"]):
            for shift in rotation["shifts"]:
                rotation_shifts.append(
                    RotationShift.from_dict(shift, num_oncall_shift_layers - idx)
                )

        return cls(
            name=generate_splunk_schedule_name(schedule),
            rotation_shifts=rotation_shifts,
            overrides=[
                Override.from_dict(override) for override in schedule["overrides"]
            ],
        )

    def to_oncall_schedule(
        self, user_id_map: dict[str, str]
    ) -> tuple[Optional[dict], list[str]]:
        """
        Convert a Schedule object to an OnCall schedule.
        Note that it also returns shifts, but these are not created at the same time as the schedule (see migrate method for more info).
        """
        shifts = []
        errors = []
        for rotation_shift in self.rotation_shifts:
            # Check if all users in the rotation exist in OnCall
            missing_user_ids = [
                user_id
                for user_id in rotation_shift.user_ids
                if user_id_map.get(user_id) is None
            ]
            if missing_user_ids:
                errors.append(
                    f"{rotation_shift.name}: Users with IDs {missing_user_ids} not found. The user(s) don't seem to exist in Grafana."
                )
                continue

            shifts.append(rotation_shift.to_oncall_shift(user_id_map))

        for override in self.overrides:
            user_id = override.user_id

            if user_id_map.get(user_id) is None:
                errors.append(
                    f"Override: User with ID '{user_id}' not found. The user doesn't seem to exist in Grafana."
                )
                continue

            shifts.append(override.to_oncall_shift(user_id_map))

        if errors:
            return None, errors

        return {
            "name": self.name,
            "type": "web",
            "team_id": None,
            "time_zone": TIME_ZONE,
            "shifts": shifts,
        }, []

    def migrate(self, user_id_map: dict[str, str]) -> dict:
        """
        Create an OnCall schedule and its shifts.
        First create the shifts, then create a schedule with shift IDs provided.
        """

        schedule, errors = self.to_oncall_schedule(user_id_map)
        assert not errors, "Unexpected errors: {}".format(errors)

        # Create shifts in OnCall
        shift_ids = [
            OnCallAPIClient.create("on_call_shifts", shift)["id"]
            for shift in schedule["shifts"]
        ]

        # Create schedule in OnCall with shift IDs provided
        schedule["shifts"] = shift_ids
        new_schedule = OnCallAPIClient.create("schedules", schedule)

        return new_schedule


@dataclass
class RotationShift:
    """
    Utility class for converting a Splunk schedule rotation layer to OnCall shifts.
    """

    name: str
    level: int

    shift_type: typing.Literal["std", "pho", "cstm"]
    start: datetime.datetime
    duration: datetime.timedelta
    mask: types.SplunkRotationShiftMask
    mask2: typing.Optional[types.SplunkRotationShiftMask]
    mask3: typing.Optional[types.SplunkRotationShiftMask]

    user_ids: list[str]

    MONDAY = "m"
    TUESDAY = "t"
    WEDNESDAY = "w"
    THURSDAY = "th"
    FRIDAY = "f"
    SATURDAY = "sa"
    SUNDAY = "su"

    SPLUNK_TO_ONCALL_DAY_MASK_MAP = {
        SUNDAY: "SU",
        MONDAY: "MO",
        TUESDAY: "TU",
        WEDNESDAY: "WE",
        THURSDAY: "TH",
        FRIDAY: "FR",
        SATURDAY: "SA",
    }

    @classmethod
    def from_dict(
        cls, rotation_shift: types.SplunkRotationShift, level: int
    ) -> "RotationShift":
        """
        Create a RotationShift object from a Splunk API response for a rotation.
        Converts Splunk datetime strings to datetime objects for easier manipulation.
        """
        return cls(
            name=rotation_shift["label"],
            level=level,
            shift_type=rotation_shift["shifttype"],
            start=_splunk_datetime_to_dt(rotation_shift["start"]),
            duration=datetime.timedelta(days=rotation_shift["duration"]),
            mask=rotation_shift["mask"],
            mask2=rotation_shift.get("mask2"),
            mask3=rotation_shift.get("mask3"),
            user_ids=[u["username"] for u in rotation_shift["shiftMembers"]],
        )

    def _construct_datetime_from_date_and_mask_time(
        self,
        date: datetime.date,
        mask: types.SplunkRotationShiftMask,
        mask_key: typing.Literal["start", "end"],
    ) -> datetime.datetime:
        mask_time = mask["time"][0][mask_key]
        return datetime.datetime.combine(
            date,
            datetime.time(hour=mask_time["hour"], minute=mask_time["minute"]),
        )

    def _calculate_partial_day_duration_from_mask(self) -> datetime.timedelta:
        """
        Calculate the duration of the shift based on the mask.
        """
        today = datetime.date.today()

        start_dt = self._construct_datetime_from_date_and_mask_time(
            today, self.mask, "start"
        )
        end_dt = self._construct_datetime_from_date_and_mask_time(
            today, self.mask, "end"
        )

        return end_dt - start_dt

    def _calculate_by_days_from_partial_day_shift_mask(self) -> list[str]:
        """
        Calculate the days of the week the shift occurs based on the mask.
        """
        return [
            self.SPLUNK_TO_ONCALL_DAY_MASK_MAP[day]
            for day, is_active in self.mask["day"].items()
            if is_active
        ]

    def _next_day_of_week(
        self, starting_date: datetime.date, day_of_week: str
    ) -> datetime.date:
        # Define a mapping of day abbreviations to their corresponding datetime weekday values
        SPLUNK_DAY_ABBREVIATION_TO_DATETIME_WEEKDAY_IDX_MAP = {
            self.MONDAY: 0,
            self.TUESDAY: 1,
            self.WEDNESDAY: 2,
            self.THURSDAY: 3,
            self.FRIDAY: 4,
            self.SATURDAY: 5,
            self.SUNDAY: 6,
        }

        # Calculate the difference between starting_date's weekday and the desired weekday
        days_until_next_day = (
            SPLUNK_DAY_ABBREVIATION_TO_DATETIME_WEEKDAY_IDX_MAP[day_of_week]
            - starting_date.weekday()
            + 7
        ) % 7

        # Calculate the date of the next desired day of the week
        return starting_date + datetime.timedelta(days=days_until_next_day)

    def _get_sole_active_day_from_mask(
        self, mask: types.SplunkRotationShiftMask
    ) -> str:
        """
        making a big assumption here, but it looks like for multi-day shifts, mask and mask3
        only have one active day each
        """
        return [day for day, is_active in mask["day"].items() if is_active][0]

    def _calculate_multi_day_duration_from_masks(self) -> datetime.timedelta:
        start_mask = self.mask
        end_mask = self.mask3

        today = datetime.date.today()
        shift_start_date = self._next_day_of_week(
            today, self._get_sole_active_day_from_mask(start_mask)
        )
        shift_end_date = self._next_day_of_week(
            shift_start_date, self._get_sole_active_day_from_mask(end_mask)
        )

        shift_start_dt = self._construct_datetime_from_date_and_mask_time(
            shift_start_date, start_mask, "start"
        )
        shift_end_dt = self._construct_datetime_from_date_and_mask_time(
            shift_end_date, end_mask, "end"
        )
        return shift_end_dt - shift_start_dt

    def to_oncall_shift(self, user_id_map: dict[str, str]) -> typing.Dict:
        frequency, interval = duration_to_frequency_and_interval(self.duration)
        start = dt_to_oncall_datetime(self.start)

        duration: datetime.timedelta
        extra_kwargs = {}

        if self.shift_type == "std":
            duration = self.duration
        elif self.shift_type == "pho":
            duration = self._calculate_partial_day_duration_from_mask()
            extra_kwargs[
                "by_day"
            ] = self._calculate_by_days_from_partial_day_shift_mask()
        elif self.shift_type == "cstm":
            num_days = self.duration.days

            if num_days != 7:
                # NOTE: we don't currently support multi-day Splunk shifts with a "hand-off" greater than one week
                # https://raintank-corp.slack.com/archives/C04JCU51NF8/p1714581046981109?thread_ts=1714580582.883559&cid=C04JCU51NF8
                raise ValueError(
                    f"Multi-day shifts with a duration greater than 7 days are not supported: {num_days} days"
                )

            duration = self._calculate_multi_day_duration_from_masks()
        else:
            raise ValueError(f"Unknown shift type: {self.shift_type}")

        return {
            "name": self.name,
            "team_id": None,
            "level": self.level,
            "type": "rolling_users",
            "rotation_start": start,
            "start": start,
            "until": None,
            "duration": int(duration.total_seconds()),
            "frequency": frequency,
            "interval": interval,
            "rolling_users": [[user_id_map[user_id]] for user_id in self.user_ids],
            "start_rotation_from_user_index": 0,
            "week_start": "MO",
            "time_zone": TIME_ZONE,
            "source": ONCALL_SHIFT_WEB_SOURCE,
            **extra_kwargs,
        }


@dataclass
class Override:
    start: datetime.datetime
    end: datetime.datetime
    user_id: str

    @classmethod
    def from_dict(cls, override: types.SplunkScheduleOverride) -> "Override":
        # convert start and end to datetime objects in UTC
        return cls(
            start=datetime.datetime.fromisoformat(override["start"]).astimezone(
                datetime.timezone.utc
            ),
            end=datetime.datetime.fromisoformat(override["end"]).astimezone(
                datetime.timezone.utc
            ),
            user_id=override["overrideOnCallUser"]["username"],
        )

    def to_oncall_shift(self, user_id_map: dict[str, str]) -> dict:
        start = dt_to_oncall_datetime(self.start)
        duration = int((self.end - self.start).total_seconds())
        user_id = user_id_map[self.user_id]

        return {
            "name": uuid4().hex,
            "team_id": None,
            "type": "override",
            "time_zone": TIME_ZONE,
            "start": start,
            "duration": duration,
            "rotation_start": start,
            "users": [user_id],
            "source": ONCALL_SHIFT_WEB_SOURCE,
        }
