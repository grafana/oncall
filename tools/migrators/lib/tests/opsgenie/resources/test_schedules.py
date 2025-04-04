from unittest.mock import patch

from lib.opsgenie.resources.schedules import (
    match_schedule,
    match_users_for_schedule,
    migrate_schedule,
)


def test_match_schedule():
    schedule = {
        "id": "s1",
        "name": "Primary Schedule",
        "timezone": "UTC",
        "rotations": [],
    }
    oncall_schedules = [
        {"id": "os1", "name": "Primary Schedule"},
        {"id": "os2", "name": "Secondary Schedule"},
    ]
    user_id_map = {}

    match_schedule(schedule, oncall_schedules, user_id_map)
    assert schedule["oncall_schedule"]["id"] == "os1"
    assert not schedule["migration_errors"]


def test_match_schedule_case_insensitive():
    schedule = {
        "id": "s1",
        "name": "Primary Schedule",
        "timezone": "UTC",
        "rotations": [],
    }
    oncall_schedules = [
        {"id": "os1", "name": "primary SCHEDULE"},
        {"id": "os2", "name": "Secondary Schedule"},
    ]
    user_id_map = {}

    match_schedule(schedule, oncall_schedules, user_id_map)
    assert schedule["oncall_schedule"]["id"] == "os1"
    assert not schedule["migration_errors"]


def test_match_users_for_schedule():
    schedule = {
        "id": "s1",
        "name": "Primary Schedule",
        "rotations": [
            {
                "participants": [
                    {"type": "user", "id": "u1"},
                    {"type": "user", "id": "u2"},
                ],
            }
        ],
    }
    users = [
        {"id": "u1", "oncall_user": {"id": "ou1"}},
        {"id": "u2", "oncall_user": None},
        {"id": "u3", "oncall_user": {"id": "ou3"}},
    ]

    match_users_for_schedule(schedule, users)
    assert len(schedule["matched_users"]) == 1
    assert schedule["matched_users"][0]["id"] == "u1"


@patch("lib.opsgenie.resources.schedules.OnCallAPIClient")
def test_migrate_schedule(mock_client):
    # Mock OnCall API responses
    mock_client.create.side_effect = [
        {"id": "or1"},  # First rotation
        {"id": "or2"},  # Second rotation
        {"id": "os1", "name": "Primary Schedule"},  # Schedule creation
    ]

    schedule = {
        "id": "s1",
        "name": "Primary Schedule",
        "timezone": "UTC",
        "rotations": [
            {
                "name": "Daily Rotation",
                "type": "daily",
                "length": 1,
                "participants": [{"type": "user", "id": "u1"}],
                "startDate": "2024-01-01T00:00:00Z",
                "enabled": True,
            },
            {
                "name": "Weekly Rotation",
                "type": "weekly",
                "length": 1,
                "participants": [{"type": "user", "id": "u2"}],
                "startDate": "2024-01-01T00:00:00Z",
                "enabled": True,
                "timeRestriction": {
                    "type": "weekday-and-time-of-day",
                    "restrictions": [
                        {
                            "startDay": "MONDAY",
                            "endDay": "FRIDAY",
                        }
                    ],
                },
            },
        ],
        "oncall_schedule": {"id": "os_old"},
    }
    user_id_map = {"u1": "ou1", "u2": "ou2"}

    migrate_schedule(schedule, user_id_map)

    # Verify schedule creation
    mock_client.delete.assert_called_once_with("schedules/os_old")

    # Verify shift creation calls
    mock_client.create.assert_any_call(
        "on_call_shifts",
        {
            "name": "Daily Rotation",
            "type": "rolling_users",
            "time_zone": "UTC",
            "team_id": None,
            "level": 1,
            "start": "2024-01-01T00:00:00",
            "duration": 86400,  # 1 day in seconds
            "frequency": "daily",
            "interval": 1,
            "rolling_users": [["ou1"]],
            "start_rotation_from_user_index": 0,
            "week_start": "MO",
            "source": 0,
        },
    )

    # Verify schedule creation with shift IDs
    mock_client.create.assert_called_with(
        "schedules",
        {
            "name": "Primary Schedule",
            "type": "web",
            "team_id": None,
            "time_zone": "UTC",
            "shifts": ["or1", "or2"],
        },
    )
