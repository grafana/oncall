from unittest.mock import patch

from lib.opsgenie.resources.escalation_policies import (
    match_escalation_policy,
    match_users_and_schedules_for_escalation_policy,
    migrate_escalation_policy,
)


def test_match_escalation_policy():
    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "rules": [],
    }
    oncall_chains = [
        {"id": "oc1", "name": "Critical Alerts"},
        {"id": "oc2", "name": "Non-Critical Alerts"},
    ]

    match_escalation_policy(policy, oncall_chains)
    assert policy["oncall_escalation_chain"]["id"] == "oc1"


def test_match_users_and_schedules_for_escalation_policy():
    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "rules": [
            {
                "recipients": [
                    {"type": "user", "id": "u1"},
                    {"type": "schedule", "id": "s1"},
                ],
            }
        ],
    }
    users = [
        {"id": "u1", "oncall_user": {"id": "ou1"}},
        {"id": "u2", "oncall_user": None},
    ]
    schedules = [
        {"id": "s1", "name": "Primary Schedule", "migration_errors": []},
        {"id": "s2", "name": "Secondary Schedule", "migration_errors": ["error"]},
    ]

    match_users_and_schedules_for_escalation_policy(policy, users, schedules)
    assert len(policy["matched_users"]) == 1
    assert policy["matched_users"][0]["id"] == "u1"
    assert len(policy["matched_schedules"]) == 1
    assert policy["matched_schedules"][0]["id"] == "s1"


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
