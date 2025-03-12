import pytest
from unittest.mock import patch, MagicMock

from lib.opsgenie.resources.schedules import migrate_schedule, _convert_rotation_type, _convert_time_restriction
from lib.opsgenie.resources.escalation_policies import migrate_escalation_policy
from lib.opsgenie.resources.integrations import migrate_integration
from lib.opsgenie.resources.notification_rules import migrate_notification_rules


@patch("lib.oncall.api_client.OnCallAPIClient")
def test_migrate_schedule(mock_client):
    # Mock OnCall API responses
    mock_client.create.side_effect = [
        {"id": "os1", "name": "Primary Schedule"},  # Schedule creation
        {"id": "or1"},  # First rotation
        {"id": "or2"},  # Second rotation
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
    mock_client.create.assert_any_call(
        "schedules",
        {
            "name": "Primary Schedule",
            "type": "web",
            "team_id": None,
            "time_zone": "UTC",
        },
    )

    # Verify rotation creation calls
    mock_client.create.assert_any_call(
        "rotations",
        {
            "schedule_id": "os1",
            "name": "Daily Rotation",
            "start": "2024-01-01T00:00:00Z",
            "duration": 86400,  # 1 day in seconds
            "frequency": "daily",
            "by_day": None,
            "users": ["ou1"],
        },
    )

    mock_client.create.assert_any_call(
        "rotations",
        {
            "schedule_id": "os1",
            "name": "Weekly Rotation",
            "start": "2024-01-01T00:00:00Z",
            "duration": 604800,  # 1 week in seconds
            "frequency": "weekly",
            "by_day": ["MO", "TU", "WE", "TH", "FR"],
            "users": ["ou2"],
        },
    )


@patch("lib.oncall.api_client.OnCallAPIClient")
def test_migrate_escalation_policy(mock_client):
    mock_client.create.side_effect = [
        {"id": "oc1"},  # Chain creation
        {"id": "op1"},  # First policy
        {"id": "op2"},  # Wait step
        {"id": "op3"},  # Second policy
    ]

    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "rules": [
            {
                "recipients": [
                    {"type": "user", "id": "u1"},
                ],
                "delay": 5,
                "isHighPriority": True,
            },
            {
                "recipients": [
                    {"type": "schedule", "id": "s1"},
                ],
                "delay": 10,
            },
        ],
        "oncall_escalation_chain": {"id": "oc_old"},
        "matched_users": [{"id": "u1", "oncall_user": {"id": "ou1"}}],
        "matched_schedules": [{"id": "s1", "oncall_schedule": {"id": "os1"}}],
    }

    migrate_escalation_policy(policy, [], [])

    # Verify chain creation
    mock_client.delete.assert_called_once_with("escalation_chains/oc_old")
    mock_client.create.assert_any_call(
        "escalation_chains",
        {
            "name": "Critical Alerts",
            "team_id": None,
        },
    )

    # Verify policy creation calls
    mock_client.create.assert_any_call(
        "escalation_policies",
        {
            "escalation_chain_id": "oc1",
            "position": 0,
            "type": "notify_persons",
            "persons_to_notify": ["ou1"],
            "important": True,
        },
    )

    mock_client.create.assert_any_call(
        "escalation_policies",
        {
            "escalation_chain_id": "oc1",
            "position": 1,
            "type": "wait",
            "duration": 300,  # 5 minutes in seconds
        },
    )

    mock_client.create.assert_any_call(
        "escalation_policies",
        {
            "escalation_chain_id": "oc1",
            "position": 2,
            "type": "notify_on_call_from_schedule",
            "schedule_id": "os1",
            "important": False,
        },
    )


@patch("lib.oncall.api_client.OnCallAPIClient")
def test_migrate_integration(mock_client):
    mock_client.create.return_value = {"id": "oi1"}

    integration = {
        "id": "i1",
        "name": "Prometheus Alerts",
        "type": "Prometheus",
        "oncall_type": "alertmanager",
        "oncall_integration": {"id": "oi_old"},
        "oncall_escalation_chain": {"id": "oc1"},
    }

    migrate_integration(integration, [])

    # Verify integration creation
    mock_client.delete.assert_called_once_with("integrations/oi_old")
    mock_client.create.assert_called_once_with(
        "integrations",
        {
            "name": "Prometheus Alerts",
            "type": "alertmanager",
            "team_id": None,
            "escalation_chain_id": "oc1",
        },
    )


@patch("lib.oncall.api_client.OnCallAPIClient")
def test_migrate_notification_rules(mock_client):
    user = {
        "id": "u1",
        "notification_rules": [
            {
                "type": "sms",
                "enabled": True,
                "delay": 5,
                "criteria": {"isHighPriority": True},
            },
            {
                "type": "voice",
                "enabled": True,
                "delay": 10,
            },
        ],
        "oncall_user": {
            "id": "ou1",
            "notification_rules": [{"id": "nr_old"}],
        },
    }

    migrate_notification_rules(user)

    # Verify old rules deletion
    mock_client.delete.assert_called_once_with("personal_notification_rules/nr_old")

    # Verify new rules creation
    mock_client.create.assert_any_call(
        "personal_notification_rules",
        {
            "user_id": "ou1",
            "type": "notify_by_sms",
            "important": True,
            "duration": 300,  # 5 minutes in seconds
        },
    )

    mock_client.create.assert_any_call(
        "personal_notification_rules",
        {
            "user_id": "ou1",
            "type": "notify_by_phone_call",
            "important": False,
            "duration": 600,  # 10 minutes in seconds
        },
    )


def test_convert_rotation_type():
    # Test daily rotation
    freq, interval = _convert_rotation_type("daily", 2)
    assert freq == "daily"
    assert interval == 172800  # 2 days in seconds

    # Test weekly rotation
    freq, interval = _convert_rotation_type("weekly", 1)
    assert freq == "weekly"
    assert interval == 604800  # 1 week in seconds

    # Test hourly rotation
    freq, interval = _convert_rotation_type("hourly", 4)
    assert freq == "hourly"
    assert interval == 14400  # 4 hours in seconds

    # Test custom rotation
    freq, interval = _convert_rotation_type("custom", 3)
    assert freq == "custom"
    assert interval == 259200  # 3 days in seconds


def test_convert_time_restriction():
    # Test weekday restriction
    restriction = {
        "type": "weekday-and-time-of-day",
        "restrictions": [
            {
                "startDay": "MONDAY",
                "endDay": "FRIDAY",
            }
        ],
    }
    days = _convert_time_restriction(restriction)
    assert days == ["MO", "TU", "WE", "TH", "FR"]

    # Test weekend restriction
    restriction = {
        "type": "weekday-and-time-of-day",
        "restrictions": [
            {
                "startDay": "SATURDAY",
                "endDay": "SUNDAY",
            }
        ],
    }
    days = _convert_time_restriction(restriction)
    assert days == ["SA", "SU"]

    # Test no restriction
    days = _convert_time_restriction({})
    assert days is None

    # Test unsupported restriction type
    days = _convert_time_restriction({"type": "custom"})
    assert days is None
