import datetime

from migrator.resources.schedules import Restriction, Schedule

user_id_map = {
    "USER_ID_1": "USER_ID_1",
    "USER_ID_2": "USER_ID_2",
    "USER_ID_3": "USER_ID_3",
}


def test_merge_restrictions():
    restrictions = [
        Restriction(
            type="daily_restriction",
            start_time_of_day=datetime.time(10, 0),
            duration=datetime.timedelta(hours=1),
            start_day_of_week=None,
        ),
        Restriction(
            type="daily_restriction",
            start_time_of_day=datetime.time(9, 0),
            duration=datetime.timedelta(hours=8),
            start_day_of_week=None,
        ),
        Restriction(
            type="daily_restriction",
            start_time_of_day=datetime.time(10, 30),
            duration=datetime.timedelta(hours=9),
            start_day_of_week=None,
        ),
        Restriction(
            type="daily_restriction",
            start_time_of_day=datetime.time(22, 0),
            duration=datetime.timedelta(hours=4),
            start_day_of_week=None,
        ),
    ]

    weekly_restrictions = []
    for restriction in restrictions:
        weekly_restrictions += restriction.to_weekly_restrictions()

    merged = Restriction.merge_restrictions(weekly_restrictions)

    expected = []
    for weekday in range(7):
        expected += [
            Restriction(
                type=Restriction.Type.WEEKLY,
                start_time_of_day=datetime.time(9, 0),
                duration=datetime.timedelta(hours=10, minutes=30),
                start_day_of_week=weekday,
            ),
            Restriction(
                type=Restriction.Type.WEEKLY,
                start_time_of_day=datetime.time(22, 0),
                duration=datetime.timedelta(hours=4),
                start_day_of_week=weekday,
            ),
        ]

    assert merged == expected


def test_current_or_next_restriction():
    restrictions = [
        Restriction(
            type=Restriction.Type.WEEKLY,
            start_time_of_day=datetime.time(10, 0),
            duration=datetime.timedelta(hours=1),
            start_day_of_week=0,
        ),
        Restriction(
            type=Restriction.Type.WEEKLY,
            start_time_of_day=datetime.time(22, 0),
            duration=datetime.timedelta(hours=28),
            start_day_of_week=5,
        ),
    ]

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 20, 10, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[0],
        datetime.datetime(2023, 2, 20, 10, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions, datetime.datetime(2023, 2, 20, 8, 0, tzinfo=datetime.timezone.utc)
    )
    assert (restriction, date) == (
        restrictions[0],
        datetime.datetime(2023, 2, 20, 10, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 20, 11, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[1],
        datetime.datetime(2023, 2, 25, 22, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 22, 11, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[1],
        datetime.datetime(2023, 2, 25, 22, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 26, 12, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[1],
        datetime.datetime(2023, 2, 25, 22, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 26, 22, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[1],
        datetime.datetime(2023, 2, 25, 22, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions, datetime.datetime(2023, 2, 27, 0, 0, tzinfo=datetime.timezone.utc)
    )
    assert (restriction, date) == (
        restrictions[1],
        datetime.datetime(2023, 2, 25, 22, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions, datetime.datetime(2023, 2, 27, 2, 0, tzinfo=datetime.timezone.utc)
    )
    assert (restriction, date) == (
        restrictions[0],
        datetime.datetime(2023, 2, 27, 10, 0, tzinfo=datetime.timezone.utc),
    )

    restrictions = [
        Restriction(
            type=Restriction.Type.WEEKLY,
            start_time_of_day=datetime.time(10, 0),
            duration=datetime.timedelta(hours=20),
            start_day_of_week=2,
        ),
    ]

    restriction, date = Restriction.current_or_next_restriction(
        restrictions,
        datetime.datetime(2023, 2, 23, 10, 0, tzinfo=datetime.timezone.utc),
    )
    assert (restriction, date) == (
        restrictions[0],
        datetime.datetime(2023, 3, 1, 10, 0, tzinfo=datetime.timezone.utc),
    )

    restriction, date = Restriction.current_or_next_restriction(
        restrictions, datetime.datetime(2023, 2, 23, 5, 0, tzinfo=datetime.timezone.utc)
    )
    assert (restriction, date) == (
        restrictions[0],
        datetime.datetime(2023, 2, 22, 10, 0, tzinfo=datetime.timezone.utc),
    )


def test_deactivated_users():
    pd_schedule = {
        "name": "No restrictions",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 1",
                "start": "2023-02-19T19:25:55Z",
                "end": None,
                "rotation_virtual_start": "2023-02-07T19:00:00Z",
                "rotation_turn_length_seconds": 1209600,
                "restrictions": [],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_DEACTIVATED"}},
                ],
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )
    assert errors == [
        "Layer 1: Users with IDs ['USER_ID_DEACTIVATED'] not found. The users probably have been deactivated in PagerDuty."
    ]


def test_no_restrictions():
    pd_schedule = {
        "name": "No restrictions",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 5",
                "start": "2023-02-19T19:25:55Z",
                "end": None,
                "rotation_virtual_start": "2023-02-07T19:00:00Z",
                "rotation_turn_length_seconds": 1209600,
                "restrictions": [],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 4",
                "start": "2023-02-21T14:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T14:00:00Z",
                "rotation_turn_length_seconds": 172800,
                "restrictions": [],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-21T19:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T18:00:00Z",
                "rotation_turn_length_seconds": 25200,
                "restrictions": [],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-19T18:08:11Z",
                "end": None,
                "rotation_virtual_start": "2023-02-15T18:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-20T17:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T17:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
        ],
    }

    expected = {
        "name": "No restrictions",
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
        "shifts": [
            {
                "level": 1,
                "type": "rolling_users",
                "rotation_start": "2023-02-20T17:00:00",
                "until": None,
                "start": "2023-02-20T17:00:00",
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 2,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:08:11",
                "until": None,
                "start": "2023-02-15T18:00:00",
                "duration": 604800,
                "frequency": "weekly",
                "interval": 1,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 3,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T19:00:00",
                "until": None,
                "start": "2023-02-19T18:00:00",
                "duration": 25200,
                "frequency": "hourly",
                "interval": 7,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 4,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T14:00:00",
                "until": None,
                "start": "2023-02-19T14:00:00",
                "duration": 172800,
                "frequency": "daily",
                "interval": 2,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 5,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T19:25:55",
                "until": None,
                "start": "2023-02-07T19:00:00",
                "duration": 1209600,
                "frequency": "weekly",
                "interval": 2,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")

    assert errors == []
    assert oncall_schedule == expected


def test_daily_with_daily_restrictions():
    pd_schedule = {
        "name": "Daily with daily restrictions",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 10",
                "start": "2023-02-21T20:00:09Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T20:00:00Z",
                "rotation_turn_length_seconds": 259200,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "17:00:00",
                        "duration_seconds": 57600,
                        "start_day_of_week": None,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 9",
                "start": "2023-02-21T17:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T17:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "15:00:00",
                        "duration_seconds": 14400,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}],
            },
            {
                "name": "Layer 8",
                "start": "2023-02-21T00:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T00:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "20:00:00",
                        "duration_seconds": 39600,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "21:00:00",
                        "duration_seconds": 25200,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "23:00:00",
                        "duration_seconds": 21600,
                        "start_day_of_week": None,
                    },
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 7",
                "start": "2023-02-19T18:49:46Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T03:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "20:00:00",
                        "duration_seconds": 39600,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 6",
                "start": "2023-02-19T18:49:46Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T18:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 25200,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "03:00:00",
                        "duration_seconds": 7200,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "04:30:00",
                        "duration_seconds": 16200,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "11:00:00",
                        "duration_seconds": 34200,
                        "start_day_of_week": None,
                    },
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 5",
                "start": "2023-02-21T14:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T14:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "04:00:00",
                        "duration_seconds": 14400,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "13:00:00",
                        "duration_seconds": 18000,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "19:00:00",
                        "duration_seconds": 12600,
                        "start_day_of_week": None,
                    },
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 4",
                "start": "2023-02-21T16:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T16:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-21T20:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-18T20:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-21T05:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T05:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-21T09:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-19T09:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
        ],
    }

    expected = {
        "name": "Daily with daily restrictions",
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
        "shifts": [
            {
                "level": 1,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T09:00:00",
                "until": None,
                "start": "2023-02-19T09:00:00",
                "duration": 28800,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 2,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T05:00:00",
                "until": None,
                "start": "2023-02-19T09:00:00",
                "duration": 28800,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 3,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T20:00:00",
                "until": None,
                "start": "2023-02-19T09:00:00",
                "duration": 28800,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 4,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T16:00:00",
                "until": None,
                "start": "2023-02-19T16:00:00",
                "duration": 3600,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 4,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T16:00:00",
                "until": None,
                "start": "2023-02-20T09:00:00",
                "duration": 25200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 5,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T14:00:00",
                "until": None,
                "start": "2023-02-19T14:00:00",
                "duration": 14400,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 5,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T14:00:00",
                "until": None,
                "start": "2023-02-19T19:00:00",
                "duration": 12600,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 5,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T14:00:00",
                "until": None,
                "start": "2023-02-20T04:00:00",
                "duration": 14400,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 5,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T14:00:00",
                "until": None,
                "start": "2023-02-20T13:00:00",
                "duration": 3600,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 6,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:49:46",
                "until": None,
                "start": "2023-02-19T18:00:00",
                "duration": 9000,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 6,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:49:46",
                "until": None,
                "start": "2023-02-20T00:00:00",
                "duration": 32400,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 6,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:49:46",
                "until": None,
                "start": "2023-02-20T11:00:00",
                "duration": 25200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 7,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:49:46",
                "until": None,
                "start": "2023-02-19T03:00:00",
                "duration": 14400,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 7,
                "type": "rolling_users",
                "rotation_start": "2023-02-19T18:49:46",
                "until": None,
                "start": "2023-02-19T20:00:00",
                "duration": 25200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 8,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T00:00:00",
                "until": None,
                "start": "2023-02-21T00:00:00",
                "duration": 25200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 8,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T00:00:00",
                "until": None,
                "start": "2023-02-21T20:00:00",
                "duration": 14400,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 9,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T17:00:00",
                "until": None,
                "start": "2023-02-21T17:00:00",
                "duration": 7200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 9,
                "type": "rolling_users",
                "rotation_start": "2023-02-21T17:00:00",
                "until": None,
                "start": "2023-02-22T15:00:00",
                "duration": 7200,
                "frequency": "daily",
                "interval": 1,
                "by_day": None,
                "rolling_users": [["USER_ID_1"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 46800,
                "frequency": "daily",
                "interval": 3,
                "level": 10,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T20:00:09",
                "start": "2023-02-21T20:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 57600,
                "frequency": "daily",
                "interval": 3,
                "level": 10,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T20:00:09",
                "start": "2023-02-22T17:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 57600,
                "frequency": "daily",
                "interval": 3,
                "level": 10,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T20:00:09",
                "start": "2023-02-23T17:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 10800,
                "frequency": "daily",
                "interval": 3,
                "level": 10,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T20:00:09",
                "start": "2023-02-24T17:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")

    assert errors == []
    assert oncall_schedule == expected


def test_weekly_with_daily_restrictions():
    pd_schedule = {
        "name": "Weekly with daily restrictions",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 6",
                "start": "2023-02-21T14:04:37Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T17:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 5",
                "start": "2023-02-21T14:04:37Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T08:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 4",
                "start": "2023-02-21T14:04:37Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T09:00:00Z",
                "rotation_turn_length_seconds": 1814400,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "22:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    },
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-20T15:23:15Z",
                "end": None,
                "rotation_virtual_start": "2023-02-15T08:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 72000,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "10:00:00",
                        "duration_seconds": 54000,
                        "start_day_of_week": None,
                    },
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "06:00:00",
                        "duration_seconds": 3600,
                        "start_day_of_week": None,
                    },
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-20T12:50:08Z",
                "end": None,
                "rotation_virtual_start": "2023-02-14T09:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-20T12:50:08Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T09:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
        ],
    }

    expected = {
        "name": "Weekly with daily restrictions",
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
        "shifts": [
            {
                "level": 1,
                "type": "rolling_users",
                "rotation_start": "2023-02-20T12:50:08",
                "until": None,
                "start": "2023-02-20T09:00:00",
                "duration": 28800,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "MO",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "level": 2,
                "type": "rolling_users",
                "rotation_start": "2023-02-20T12:50:08",
                "until": None,
                "start": "2023-02-14T09:00:00",
                "duration": 28800,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "start_rotation_from_user_index": 0,
                "week_start": "TU",
                "time_zone": "UTC",
                "source": 0,
            },
            {
                "duration": 72000,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 3,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "rotation_start": "2023-02-20T15:23:15",
                "start": "2023-02-15T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "WE",
                "source": 0,
            },
            {
                "duration": 3600,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 3,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "rotation_start": "2023-02-20T15:23:15",
                "start": "2023-02-16T06:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TH",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-21T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-28T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-03-07T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-21T22:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-28T22:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 3,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-03-07T22:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 5,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-21T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "TU",
                "source": 0,
            },
            {
                "duration": 28800,
                "frequency": "weekly",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"],
                "level": 6,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T14:04:37",
                "start": "2023-02-22T09:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "WE",
                "source": 0,
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_daily_with_weekly_restrictions():
    pd_schedule = {
        "name": "Daily with weekly restrictions",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 4",
                "start": "2023-02-21T19:42:57Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T05:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "05:00:00",
                        "duration_seconds": 172800,
                        "start_day_of_week": 2,
                    },
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "05:00:00",
                        "duration_seconds": 172800,
                        "start_day_of_week": 6,
                    },
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-20T17:48:08Z",
                "end": None,
                "rotation_virtual_start": "2023-02-13T00:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 432000,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-21T16:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T16:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "16:00:00",
                        "duration_seconds": 86400,
                        "start_day_of_week": 1,
                    },
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "16:00:00",
                        "duration_seconds": 172800,
                        "start_day_of_week": 3,
                    },
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-21T17:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T17:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "17:00:00",
                        "duration_seconds": 86400,
                        "start_day_of_week": 1,
                    },
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "17:00:00",
                        "duration_seconds": 259200,
                        "start_day_of_week": 3,
                    },
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
        ],
    }

    expected = {
        "name": "Daily with weekly restrictions",
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
        "shifts": [
            {
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "by_day": ["MO", "WE", "TH", "FR"],
                "level": 1,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T17:00:00",
                "start": "2023-02-20T17:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "by_day": ["MO", "WE", "TH"],
                "level": 2,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T16:00:00",
                "start": "2023-02-20T16:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "by_day": ["MO", "TU", "WE", "TH", "FR"],
                "level": 3,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-20T17:48:08",
                "start": "2023-02-13T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "by_day": ["TU", "WE", "SA", "SU"],
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T19:42:57",
                "start": "2023-02-21T05:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_weekly_with_weekly_restrictions():
    pd_schedule = {
        "name": "Weekly (weekly)",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 6",
                "start": "2023-02-21T13:32:17Z",
                "end": None,
                "rotation_virtual_start": "2023-02-24T13:00:00Z",
                "rotation_turn_length_seconds": 1814400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 349200,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 5",
                "start": "2023-02-21T13:26:21Z",
                "end": None,
                "rotation_virtual_start": "2023-02-25T13:00:00Z",
                "rotation_turn_length_seconds": 1814400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 313200,
                        "start_day_of_week": 6,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 4",
                "start": "2023-02-21T11:14:44Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T03:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "10:00:00",
                        "duration_seconds": 154800,
                        "start_day_of_week": 6,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-20T18:10:46Z",
                "end": None,
                "rotation_virtual_start": "2023-02-14T05:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 86400,
                        "start_day_of_week": 3,
                    },
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 298800,
                        "start_day_of_week": 5,
                    },
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-20T18:10:46Z",
                "end": None,
                "rotation_virtual_start": "2023-02-16T17:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "17:00:00",
                        "duration_seconds": 345600,
                        "start_day_of_week": 6,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-20T18:10:46Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T00:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 432000,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
        ],
    }

    expected = {
        "name": "Weekly (weekly)",
        "shifts": [
            {
                "by_day": None,
                "duration": 432000,
                "frequency": "weekly",
                "interval": 1,
                "level": 1,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-20T18:10:46",
                "start": "2023-02-20T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 345600,
                "frequency": "weekly",
                "interval": 1,
                "level": 2,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-20T18:10:46",
                "start": "2023-02-18T17:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 86400,
                "frequency": "weekly",
                "interval": 1,
                "level": 3,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "rotation_start": "2023-02-20T18:10:46",
                "start": "2023-02-15T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 298800,
                "frequency": "weekly",
                "interval": 1,
                "level": 3,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"]],
                "rotation_start": "2023-02-20T18:10:46",
                "start": "2023-02-17T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 7200,
                "frequency": "weekly",
                "interval": 1,
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T11:14:44",
                "start": "2023-02-20T03:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 147600,
                "frequency": "weekly",
                "interval": 1,
                "level": 4,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T11:14:44",
                "start": "2023-02-25T10:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 266400,
                "frequency": "weekly",
                "interval": 3,
                "level": 5,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:26:21",
                "start": "2023-02-25T13:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 313200,
                "frequency": "weekly",
                "interval": 3,
                "level": 5,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:26:21",
                "start": "2023-03-04T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 313200,
                "frequency": "weekly",
                "interval": 3,
                "level": 5,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:26:21",
                "start": "2023-03-11T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 46800,
                "frequency": "weekly",
                "interval": 3,
                "level": 5,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:26:21",
                "start": "2023-03-18T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 349200,
                "frequency": "weekly",
                "interval": 3,
                "level": 6,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:32:17",
                "start": "2023-02-27T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 349200,
                "frequency": "weekly",
                "interval": 3,
                "level": 6,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:32:17",
                "start": "2023-03-06T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
            {
                "by_day": None,
                "duration": 349200,
                "frequency": "weekly",
                "interval": 3,
                "level": 6,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T13:32:17",
                "start": "2023-03-13T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
        ],
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_errors():
    pd_schedule = {
        "name": "Errors",
        "time_zone": "Europe/London",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 11",
                "start": "2023-02-21T17:39:43Z",
                "end": None,
                "rotation_virtual_start": "2023-02-18T00:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 43200,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 10",
                "start": "2023-02-21T17:39:43Z",
                "end": None,
                "rotation_virtual_start": "2023-02-18T16:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 403200,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 9",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T11:00:00Z",
                "rotation_turn_length_seconds": 25200,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}],
            },
            {
                "name": "Layer 8",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T11:00:00Z",
                "rotation_turn_length_seconds": 25200,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 345600,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}],
            },
            {
                "name": "Layer 7",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T11:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 345600,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}],
            },
            {
                "name": "Layer 6",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T11:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}],
            },
            {
                "name": "Layer 5",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T11:00:00Z",
                "rotation_turn_length_seconds": 25200,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 349200,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 4",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T10:00:00Z",
                "rotation_turn_length_seconds": 25200,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 64800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 3",
                "start": "2023-02-21T13:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-21T13:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [
                    {
                        "type": "weekly_restriction",
                        "start_time_of_day": "00:00:00",
                        "duration_seconds": 406800,
                        "start_day_of_week": 1,
                    }
                ],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            },
            {
                "name": "Layer 2",
                "start": "2023-02-21T11:06:04Z",
                "end": None,
                "rotation_virtual_start": "2023-02-20T10:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 7200,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
            {
                "name": "Layer 1",
                "start": "2023-02-21T12:00:00Z",
                "end": None,
                "rotation_virtual_start": "2023-02-15T12:00:00Z",
                "rotation_turn_length_seconds": 604800,
                "restrictions": [
                    {
                        "type": "daily_restriction",
                        "start_time_of_day": "09:00:00",
                        "duration_seconds": 28800,
                        "start_day_of_week": None,
                    }
                ],
                "users": [{"user": {"id": "USER_ID_1"}}, {"user": {"id": "USER_ID_2"}}],
            },
        ],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == [
        "Layer 1: Cannot migrate 1-weekly rotation with daily restrictions that are split by handoff.",
        "Layer 2: Cannot migrate 1-weekly rotation with daily restrictions that are split by handoff.",
        "Layer 3: Cannot migrate 1-daily rotation with weekly restrictions that start at a different time than the shift start.",
        "Layer 4: Cannot migrate 7-hourly rotation with daily restrictions.",
        "Layer 5: Cannot migrate 7-hourly rotation with weekly restrictions.",
        "Layer 6: Cannot migrate 1-weekly rotation with daily restrictions that are split by handoff. Layer has a single user, consider simplifying the rotation in PD.",
        "Layer 7: Cannot migrate 1-daily rotation with weekly restrictions that start at a different time than the shift start. Layer has a single user, consider simplifying the rotation in PD.",
        "Layer 8: Cannot migrate 7-hourly rotation with weekly restrictions. Layer has a single user, consider simplifying the rotation in PD.",
        "Layer 9: Cannot migrate 7-hourly rotation with daily restrictions. Layer has a single user, consider simplifying the rotation in PD.",
        "Layer 10: Cannot migrate 1-daily rotation with weekly restrictions that start at a different time than the shift start.",
        "Layer 11: Cannot migrate 1-daily rotation with weekly restrictions that have durations that are not a multiple of a 24 hours.",
    ]
    assert oncall_schedule is None


def test_time_zone():
    pd_schedule = {
        "name": "Time zone",
        "time_zone": "Europe/Paris",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 1",
                "start": "2023-02-21T17:39:43Z",
                "end": None,
                "rotation_virtual_start": "2023-02-18T00:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            }
        ],
    }

    expected = {
        "name": "Time zone",
        "shifts": [
            {
                "duration": 86400,
                "frequency": "daily",
                "interval": 1,
                "level": 1,
                "rolling_users": [["USER_ID_1"], ["USER_ID_2"], ["USER_ID_3"]],
                "rotation_start": "2023-02-21T17:39:43",
                "start": "2023-02-18T00:00:00",
                "start_rotation_from_user_index": 0,
                "time_zone": "UTC",
                "type": "rolling_users",
                "until": None,
                "week_start": "MO",
                "source": 0,
            },
        ],
        "team_id": None,
        "time_zone": "Europe/Paris",
        "type": "web",
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_removed_layers():
    pd_schedule = {
        "name": "Removed layer",
        "time_zone": "Europe/Paris",
        "overrides": [],
        "schedule_layers": [
            {
                "name": "Layer 1",
                "start": "2023-02-21T17:39:43Z",
                "end": "2023-02-21T17:39:43Z",
                "rotation_virtual_start": "2023-02-18T00:00:00Z",
                "rotation_turn_length_seconds": 86400,
                "restrictions": [],
                "users": [
                    {"user": {"id": "USER_ID_1"}},
                    {"user": {"id": "USER_ID_2"}},
                    {"user": {"id": "USER_ID_3"}},
                ],
            }
        ],
    }

    expected = {
        "name": "Removed layer",
        "shifts": [],
        "team_id": None,
        "time_zone": "Europe/Paris",
        "type": "web",
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_overrides():
    pd_schedule = {
        "name": "Overrides",
        "time_zone": "Europe/London",
        "overrides": [
            {
                "start": "2023-03-02T11:00:00",
                "end": "2023-03-02T12:00:00",
                "user": {"id": "USER_ID_1"},
            },
            {
                "start": "2023-03-02T11:00:00+00:00",
                "end": "2023-03-02T12:00:00+00:00",
                "user": {"id": "USER_ID_1"},
            },
            {
                "start": "2023-03-02T12:00:00+01:00",
                "end": "2023-03-02T13:00:00+01:00",
                "user": {"id": "USER_ID_1"},
            },
            {
                "start": "2023-03-02T10:00:00-01:00",
                "end": "2023-03-02T11:00:00-01:00",
                "user": {"id": "USER_ID_1"},
            },
        ],
        "schedule_layers": [],
    }

    expected = {
        "name": "Overrides",
        "shifts": [
            {
                "team_id": None,
                "duration": 3600,
                "users": ["USER_ID_1"],
                "rotation_start": "2023-03-02T11:00:00",
                "start": "2023-03-02T11:00:00",
                "time_zone": "UTC",
                "type": "override",
                "source": 0,
            },
        ]
        * 4,  # all shifts are the same
        "team_id": None,
        "time_zone": "Europe/London",
        "type": "web",
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == []

    for shift in oncall_schedule["shifts"]:
        shift.pop("name")
    assert oncall_schedule == expected


def test_override_deactivated_user():
    pd_schedule = {
        "name": "Overrides",
        "time_zone": "Europe/London",
        "overrides": [
            {
                "start": "2023-03-02T11:00:00",
                "end": "2023-03-02T12:00:00",
                "user": {"id": "USER_ID_4"},
            },
        ],
        "schedule_layers": [],
    }

    oncall_schedule, errors = Schedule.from_dict(pd_schedule).to_oncall_schedule(
        user_id_map
    )

    assert errors == [
        "Override: User with ID 'USER_ID_4' not found. The user probably has been deactivated in PagerDuty."
    ]
    assert oncall_schedule is None
