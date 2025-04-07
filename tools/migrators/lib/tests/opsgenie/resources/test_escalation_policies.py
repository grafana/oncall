from unittest.mock import call, patch

from lib.opsgenie.resources.escalation_policies import (
    match_escalation_policy,
    match_users_and_schedules_for_escalation_policy,
    migrate_escalation_policy,
)


def test_match_escalation_policy():
    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "ownerTeam": {
            "name": "Team A",
        },
        "rules": [],
    }
    oncall_chains = [
        {"id": "oc1", "name": "Team A - Critical Alerts"},
        {"id": "oc2", "name": "Team B - Non-Critical Alerts"},
    ]

    match_escalation_policy(policy, oncall_chains)
    assert policy["oncall_escalation_chain"]["id"] == "oc1"


def test_match_users_and_schedules_for_escalation_policy():
    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "ownerTeam": {
            "name": "Team A",
        },
        "rules": [
            {
                "recipient": {"type": "user", "id": "u1"},
            },
            {
                "recipient": {"type": "schedule", "id": "s1"},
            },
        ],
        "matched_users": [],
        "matched_schedules": [],
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


@patch("lib.opsgenie.resources.escalation_policies.OnCallAPIClient")
def test_migrate_escalation_policy(mock_client):
    mock_client.create.return_value = {"id": "oc1"}

    policy = {
        "id": "ep1",
        "name": "Critical Alerts",
        "ownerTeam": {
            "name": "Team A",
        },
        "rules": [
            {
                "recipient": {
                    "type": "user",
                    "id": "u1",
                },
                "notifyType": "default",
                "delay": {
                    "timeAmount": 5,
                },
            },
            {
                "recipient": {
                    "type": "schedule",
                    "id": "s1",
                },
                "notifyType": "default",
                "delay": {
                    "timeAmount": 12,
                },
            },
            {
                "recipient": {
                    "type": "user",
                    "id": "u2",
                },
                "notifyType": "somethingElse",
            },
        ],
        "oncall_escalation_chain": {"id": "oc_old"},
        "matched_users": [{"id": "u1", "oncall_user": {"id": "ou1"}}],
        "matched_schedules": [{"id": "s1", "oncall_schedule": {"id": "os1"}}],
    }

    # Create test data
    users = [{"id": "u1", "oncall_user": {"id": "ou1"}}]
    schedules = [{"id": "s1", "oncall_schedule": {"id": "os1"}}]

    migrate_escalation_policy(policy, users, schedules)

    # Verify that existing chain is deleted
    mock_client.delete.assert_called_once_with("escalation_chains/oc_old")

    mock_client.create.assert_has_calls(
        [
            # Verify new escalation chain is created
            call(
                "escalation_chains",
                {
                    "name": "Team A - Critical Alerts",
                    "team_id": None,
                },
            ),
            # Verify first wait and policy steps are created
            call(
                "escalation_policies",
                {
                    "escalation_chain_id": "oc1",
                    "position": 0,
                    "type": "wait",
                    "duration": 300,  # 5 minutes in seconds
                },
            ),
            call(
                "escalation_policies",
                {
                    "escalation_chain_id": "oc1",
                    "position": 1,
                    "type": "notify_persons",
                    "persons_to_notify": ["ou1"],
                    "important": False,
                },
            ),
            # Verify second policy and wait step
            call(
                "escalation_policies",
                {
                    "escalation_chain_id": "oc1",
                    "position": 2,
                    "type": "wait",
                    "duration": 900,  # 15 minutes in seconds
                },
            ),
            call(
                "escalation_policies",
                {
                    "escalation_chain_id": "oc1",
                    "position": 3,
                    "type": "notify_on_call_from_schedule",
                    "notify_on_call_from_schedule": "os1",
                    "important": False,
                },
            ),
        ],
        any_order=False,  # Order of calls is important
    )
