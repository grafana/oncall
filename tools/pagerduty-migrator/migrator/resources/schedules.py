import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import uuid4

from migrator import oncall_api_client
from migrator.config import (
    SCHEDULE_MIGRATION_MODE,
    SCHEDULE_MIGRATION_MODE_ICAL,
    SCHEDULE_MIGRATION_MODE_WEB,
)


def match_schedule(
    schedule: dict, oncall_schedules: list[dict], user_id_map: dict[str, str]
) -> None:
    oncall_schedule = None
    for candidate in oncall_schedules:
        if schedule["name"].lower().strip() == candidate["name"].lower().strip():
            oncall_schedule = candidate

    schedule["migration_errors"] = []
    if SCHEDULE_MIGRATION_MODE == SCHEDULE_MIGRATION_MODE_WEB:
        _, errors = Schedule.from_dict(schedule).to_oncall_schedule(user_id_map)
        schedule["migration_errors"] = errors

    schedule["oncall_schedule"] = oncall_schedule


def migrate_schedule(schedule: dict, user_id_map: dict[str, str]) -> None:
    if schedule["oncall_schedule"]:
        oncall_api_client.delete(
            "schedules/{}".format(schedule["oncall_schedule"]["id"])
        )

    if SCHEDULE_MIGRATION_MODE == SCHEDULE_MIGRATION_MODE_WEB:
        # Migrate shifts
        oncall_schedule = Schedule.from_dict(schedule).migrate(user_id_map)
    elif SCHEDULE_MIGRATION_MODE == SCHEDULE_MIGRATION_MODE_ICAL:
        # Migrate using ICal URL
        payload = {
            "name": schedule["name"],
            "type": "ical",
            "ical_url_primary": schedule["http_cal_url"],
            "team_id": None,
        }
        oncall_schedule = oncall_api_client.create("schedules", payload)
    else:
        raise ValueError("Invalid schedule migration mode")

    schedule["oncall_schedule"] = oncall_schedule


def duration_to_frequency_and_interval(duration: datetime.timedelta) -> tuple[str, int]:
    """
    Convert a duration to shift frequency and interval.
    For example, 1 day duration returns ("daily", 1), 14 days returns ("weekly", 2),
    """
    seconds = int(duration.total_seconds())

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


def _pd_datetime_to_dt(text: str) -> datetime.datetime:
    """
    Convert a PagerDuty datetime string to a datetime object.
    """
    dt = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    return dt.replace(tzinfo=datetime.timezone.utc)


def _dt_to_oncall_datetime(dt: datetime.datetime) -> str:
    """
    Convert a datetime object to an OnCall datetime string.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


@dataclass
class Schedule:
    """
    Utility class for converting a PagerDuty schedule to an OnCall schedule.
    A PagerDuty schedule has multiple layers, each with a rotation of users.
    """

    name: str
    time_zone: str
    layers: list["Layer"]
    overrides: list["Override"]

    @classmethod
    def from_dict(cls, schedule: dict) -> "Schedule":
        """
        Create a Schedule object from a PagerDuty API response for a schedule.
        """

        layers = []
        # PagerDuty API returns layers in reverse order (e.g. Layer 3, Layer 2, Layer 1)
        for level, layer_dict in enumerate(
            reversed(schedule["schedule_layers"]), start=1
        ):
            layer = Layer.from_dict(layer_dict, level)

            # skip any layers that have already ended
            if layer.end and layer.end < datetime.datetime.now(datetime.timezone.utc):
                continue

            layers.append(layer)

        overrides = []
        for override in schedule["overrides"]:
            overrides.append(Override.from_dict(override))

        return cls(
            name=schedule["name"],
            time_zone=schedule["time_zone"],
            layers=layers,
            overrides=overrides,
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
        for layer in self.layers:
            # Check if all users in the layer exist in PD
            deactivated_user_ids = [
                user_id for user_id in layer.user_ids if user_id not in user_id_map
            ]
            if deactivated_user_ids:
                errors.append(
                    f"{layer.name}: Users with IDs {deactivated_user_ids} not found. The users probably have been deactivated in PagerDuty."
                )
                continue

            # A single PagerDuty layer can result in multiple OnCall shifts
            layer_shifts, error = layer.to_oncall_shifts(user_id_map)

            if layer_shifts:
                shifts += layer_shifts

            if error:
                error_text = f"{layer.name}: {error}"

                # If a layer has a single user, it's likely can be easily tweaked in PD to make it possible to migrate
                if len(set(layer.user_ids)) == 1:
                    error_text += " Layer has a single user, consider simplifying the rotation in PD."

                errors.append(error_text)

        for override in self.overrides:
            if override.user_id not in user_id_map:
                errors.append(
                    f"Override: User with ID '{override.user_id}' not found. The user probably has been deactivated in PagerDuty."
                )
                continue

            shifts.append(override.to_oncall_shift(user_id_map))

        if errors:
            return None, errors

        return {
            "name": self.name,
            "type": "web",
            "team_id": None,
            "time_zone": self.time_zone,
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
        shift_ids = []
        for shift in schedule["shifts"]:
            created_shift = oncall_api_client.create("on_call_shifts", shift)
            shift_ids.append(created_shift["id"])

        # Create schedule in OnCall with shift IDs provided
        schedule["shifts"] = shift_ids
        new_schedule = oncall_api_client.create("schedules", schedule)

        return new_schedule


@dataclass
class Layer:
    """
    Utility class for converting a PagerDuty schedule layer to OnCall shifts.
    """

    name: str
    level: int

    rotation_virtual_start: datetime.datetime
    rotation_turn_length: datetime.timedelta

    start: datetime.datetime
    end: Optional[datetime.datetime]

    user_ids: list[str]
    restrictions: list["Restriction"]

    @classmethod
    def from_dict(cls, layer: dict, level: int) -> "Layer":
        """
        Create a Layer object from a PagerDuty API response for a schedule layer.
        Converts PagerDuty datetime strings to datetime objects for easier manipulation.
        """
        return cls(
            name=layer["name"],
            level=level,
            rotation_virtual_start=_pd_datetime_to_dt(layer["rotation_virtual_start"]),
            rotation_turn_length=datetime.timedelta(
                seconds=layer["rotation_turn_length_seconds"]
            ),
            start=_pd_datetime_to_dt(layer["start"]),
            end=_pd_datetime_to_dt(layer["end"]) if layer["end"] else None,
            user_ids=[u["user"]["id"] for u in layer["users"]],
            restrictions=[Restriction.from_dict(r) for r in layer["restrictions"]],
        )

    def to_oncall_shifts(
        self, user_id_map: dict[str, str]
    ) -> tuple[Optional[list[dict]], Optional[str]]:
        frequency, interval = duration_to_frequency_and_interval(
            self.rotation_turn_length
        )
        rolling_users = []
        for user_id in self.user_ids:
            oncall_user_id = user_id_map[user_id]
            rolling_users.append([oncall_user_id])

        if not self.restrictions:
            return [
                {
                    "name": uuid4().hex,
                    "level": self.level,
                    "type": "rolling_users",
                    "rotation_start": _dt_to_oncall_datetime(self.start),
                    "until": _dt_to_oncall_datetime(self.end) if self.end else None,
                    "start": _dt_to_oncall_datetime(self.rotation_virtual_start),
                    "duration": int(self.rotation_turn_length.total_seconds()),
                    "frequency": frequency,
                    "interval": interval,
                    "rolling_users": rolling_users,
                    "start_rotation_from_user_index": 0,
                    "week_start": "MO",
                    "time_zone": "UTC",
                    "source": 0,  # 0 is alias for "web"
                }
            ], None

        restrictions_type = self.restrictions[0].type

        if (frequency, restrictions_type) in (
            ("daily", Restriction.Type.DAILY),
            ("weekly", Restriction.Type.WEEKLY),
        ):
            # TODO: some of this can use by_day?
            shifts, _ = self._generate_shifts(unique=False)
            shifts = [(s[0], s[1], "MO", None) for s in shifts]

        elif frequency == "weekly" and restrictions_type == Restriction.Type.DAILY:
            shifts, is_split = self._generate_shifts(unique=True)

            if is_split:
                return (
                    None,
                    f"Cannot migrate {interval}-weekly rotation with daily restrictions that are split by handoff.",
                )

            # repeat ["MO", "TU", "WE", "TH", "FR", "SA", "SU"] shift for the number of weeks in the rotation
            shifts_for_multiple_weeks = []
            for shift in shifts:
                for week in range(interval):
                    start = shift[0] + datetime.timedelta(weeks=week)
                    end = shift[1] + datetime.timedelta(weeks=week)
                    shifts_for_multiple_weeks.append((start, end))

            shifts = [
                (
                    shift[0],
                    shift[1],
                    ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][
                        shift[0].date().weekday()
                    ],
                    ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                )
                for shift in shifts_for_multiple_weeks
            ]

        elif (
            frequency == "daily"
            and restrictions_type == Restriction.Type.WEEKLY
            and interval == 1
        ):
            # the only case when it's possible to migrate a daily rotation with weekly restrictions
            # is when the restrictions start at the same time as the shift start
            # and the restrictions are a multiple of 24 hours
            restrictions = Restriction.merge_restrictions(self.restrictions)
            for restriction in restrictions:
                if (
                    not restriction.start_time_of_day
                    == self.rotation_virtual_start.time()
                ):
                    return (
                        None,
                        f"Cannot migrate {interval}-daily rotation with weekly restrictions that start at a different time than the shift start.",
                    )
                if not restriction.duration % datetime.timedelta(
                    days=1
                ) == datetime.timedelta(0):
                    return (
                        None,
                        f"Cannot migrate {interval}-daily rotation with weekly restrictions that have durations that are not a multiple of a 24 hours.",
                    )

            # get the first restriction and use its start time as the start of the shift
            restriction, shift_start = Restriction.current_or_next_restriction(
                restrictions, self.rotation_virtual_start
            )
            shift_end = shift_start + datetime.timedelta(days=1)

            # determine which days of the week are covered
            by_day = set()
            for restriction in restrictions:
                days = restriction.duration // datetime.timedelta(days=1)

                for day in range(days):
                    weekday = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"][
                        (restriction.start_day_of_week + day) % 7
                    ]
                    by_day.add(weekday)

            # sort by_day so that the order is always the same
            by_day = sorted(
                list(by_day),
                key=lambda d: ["MO", "TU", "WE", "TH", "FR", "SA", "SU"].index(d),
            )

            shifts = [(shift_start, shift_end, "MO", by_day)]

        else:
            restrictions_type_verbal = (
                "daily" if restrictions_type == Restriction.Type.DAILY else "weekly"
            )
            return (
                None,
                f"Cannot migrate {interval}-{frequency} rotation with {restrictions_type_verbal} restrictions.",
            )

        payloads = []
        for shift in shifts:
            payload = {
                "name": uuid4().hex,
                "level": self.level,
                "type": "rolling_users",
                "rotation_start": _dt_to_oncall_datetime(self.start),
                "until": _dt_to_oncall_datetime(self.end) if self.end else None,
                "start": _dt_to_oncall_datetime(shift[0]),
                "duration": int((shift[1] - shift[0]).total_seconds()),
                "frequency": frequency,
                "interval": interval,
                "by_day": shift[3],
                "rolling_users": rolling_users,
                "start_rotation_from_user_index": 0,
                "week_start": shift[2],
                "time_zone": "UTC",
                "source": 0,  # 0 is alias for "web"
            }
            payloads.append(payload)
        return payloads, None

    def _generate_shifts(
        self, unique: bool = True
    ) -> tuple[list[tuple[datetime.datetime, datetime.datetime]], bool]:
        """
        Returns a list of (start, end) tuples representing the shifts in this layer.
        Note that these are not the actual shifts for OnCall API but rather a list of
        unique intervals generated by traversing the restrictions.

        Also returns a boolean indicating whether there are restrictions split by on-call handoff.
        """

        start = self.rotation_virtual_start
        end = self.rotation_virtual_start + self.rotation_turn_length

        # Convert restrictions to weekly restrictions, then merge overlapping ones
        restrictions = []
        for restriction in self.restrictions:
            restrictions += restriction.to_weekly_restrictions()
        restrictions = Restriction.merge_restrictions(restrictions)

        is_split = False
        current = start
        shifts = []
        unique_shift_times = []

        while current < end:
            restriction, restriction_start = Restriction.current_or_next_restriction(
                restrictions, current
            )
            restriction_end = restriction_start + restriction.duration

            shift_start = max(current, restriction_start)
            shift_end = min(restriction_end, end)

            # If the next restriction starts after the end of the rotation or shift is empty, we're done
            if restriction_start > end or shift_start == shift_end:
                break

            # Check if restriction is split by handoff
            if (shift_start == start and shift_start > restriction_start) or (
                shift_end == end and shift_end < restriction_end
            ):
                is_split = True

            shift = (shift_start, shift_end)

            # check that we haven't already added this shift
            if (
                not unique
                or (shift[0].time(), shift[1].time()) not in unique_shift_times
            ):
                shifts.append(shift)
                unique_shift_times.append((shift[0].time(), shift[1].time()))

            current = shift_end

        return shifts, is_split


@dataclass
class Restriction:
    """
    Utility class for representing a restriction on a rotation in PagerDuty.
    """

    class Type(Enum):
        DAILY = "daily_restriction"
        WEEKLY = "weekly_restriction"

    type: Type
    start_time_of_day: datetime.time
    duration: datetime.timedelta
    start_day_of_week: Optional[int]  # this is only present for weekly restrictions

    @classmethod
    def from_dict(cls, restriction: dict) -> "Restriction":
        """
        Create a Restriction object from PagerDuty's API representation.
        Converts PagerDuty datetime strings to datetime objects for easier manipulation as well.
        """

        # PagerDuty's API uses 1-indexed days of the week, converting to 0-indexed for ease of use
        start_day_of_week = restriction.get("start_day_of_week")
        if start_day_of_week is not None:
            start_day_of_week -= 1

        return cls(
            type=Restriction.Type(restriction["type"]),
            start_time_of_day=datetime.time.fromisoformat(
                restriction["start_time_of_day"]
            ),
            duration=datetime.timedelta(seconds=restriction["duration_seconds"]),
            start_day_of_week=start_day_of_week,
        )

    def to_weekly_restrictions(self) -> list["Restriction"]:
        """
        Convert a daily restriction to a list of weekly restrictions.
        Daily restriction is basically 7 weekly restrictions with the same start time and duration,
        but different days of the week (e.g. 9am-5pm daily restriction is the same as 9am-5pm on Monday, 9am-5pm on Tuesday, etc.)

        Converting to weekly restrictions makes it easier to work with restrictions and only care about weekly ones.
        """

        if self.type == Restriction.Type.WEEKLY:
            return [self]
        else:
            return [
                Restriction(
                    type=Restriction.Type.WEEKLY,
                    start_time_of_day=self.start_time_of_day,
                    duration=self.duration,
                    start_day_of_week=day,
                )
                for day in range(7)
            ]

    @staticmethod
    def merge_restrictions(restrictions: list["Restriction"]) -> list["Restriction"]:
        """
        Merge a list of weekly restrictions into a list of the fewest possible weekly restrictions that cover the same time period.
        Example: (9am - 5pm restriction on Monday, 10am - 4pm restriction on Monday) -> (9am - 5pm restriction on Monday).

        Only works on weekly restrictions, as daily restrictions are converted to weekly restrictions first.
        """

        assert all(r.type == Restriction.Type.WEEKLY for r in restrictions)

        restrictions = sorted(
            restrictions, key=lambda r: (r.start_day_of_week, r.start_time_of_day)
        )
        merged = []

        for restriction in restrictions:
            restriction_start = datetime.datetime.combine(
                datetime.date.min
                + datetime.timedelta(days=restriction.start_day_of_week),
                restriction.start_time_of_day,
            )
            restriction_end = restriction_start + restriction.duration

            if not merged:
                merged.append(restriction)
                continue

            last = merged[-1]
            last_start = datetime.datetime.combine(
                datetime.date.min + datetime.timedelta(days=last.start_day_of_week),
                last.start_time_of_day,
            )
            last_end = last_start + last.duration

            if last_end < restriction_start:
                merged.append(restriction)
            else:
                restriction.start_day_of_week = last_start.weekday()
                restriction.start_time_of_day = last_start.time()
                restriction.duration = max(last_end, restriction_end) - last_start
                merged = merged[:-1] + [restriction]

        return merged

    @staticmethod
    def current_or_next_restriction(
        restrictions: list["Restriction"], dt: datetime.datetime
    ) -> tuple["Restriction", datetime.datetime]:
        """
        Get the current or next restriction for a given datetime.
        This is useful for finding all the restrictions that apply to a given rotation shift.
        """
        assert all(r.type == Restriction.Type.WEEKLY for r in restrictions)

        for weeks in (-1, 0, 1):  # check last week, this week, and next week
            for restriction in restrictions:
                restriction_date = (
                    dt.date()
                    - datetime.timedelta(days=dt.weekday())
                    + datetime.timedelta(days=restriction.start_day_of_week)
                    + datetime.timedelta(weeks=weeks)
                )
                restriction_start = datetime.datetime.combine(
                    restriction_date,
                    restriction.start_time_of_day,
                    tzinfo=datetime.timezone.utc,
                )
                restriction_end = restriction_start + restriction.duration

                if restriction_end > dt:
                    return restriction, restriction_start

        # there should always be a restriction
        raise ValueError("No restriction found for given datetime")


@dataclass
class Override:
    start: datetime.datetime
    end: datetime.datetime
    user_id: str

    @classmethod
    def from_dict(cls, override: dict) -> "Override":
        # convert start and end to datetime objects in UTC
        start = datetime.datetime.fromisoformat(override["start"]).astimezone(
            datetime.timezone.utc
        )
        end = datetime.datetime.fromisoformat(override["end"]).astimezone(
            datetime.timezone.utc
        )

        return cls(start=start, end=end, user_id=override["user"]["id"])

    def to_oncall_shift(self, user_id_map: dict[str, str]) -> dict:
        start = _dt_to_oncall_datetime(self.start)
        duration = int((self.end - self.start).total_seconds())
        user_id = user_id_map[self.user_id]

        return {
            "name": uuid4().hex,
            "team_id": None,
            "type": "override",
            "time_zone": "UTC",
            "start": start,
            "duration": duration,
            "rotation_start": start,
            "users": [user_id],
            "source": 0,  # 0 is alias for "web"
        }
