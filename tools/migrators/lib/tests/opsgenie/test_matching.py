import pytest

from lib.opsgenie.resources.schedules import match_schedule
from lib.opsgenie.resources.escalation_policies import match_escalation_policy
from lib.opsgenie.resources.integrations import (
    match_integration,
    match_integration_type,
    match_escalation_policy_for_integration,
)
from lib.opsgenie.resources.users import (
    match_users_for_schedule,
    match_users_and_schedules_for_escalation_policy,
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


def test_match_integration():
    integration = {
        "id": "i1",
        "name": "Prometheus Alerts",
        "type": "Prometheus",
    }
    oncall_integrations = [
        {"id": "oi1", "name": "Prometheus Alerts"},
        {"id": "oi2", "name": "Datadog Alerts"},
    ]

    match_integration(integration, oncall_integrations)
    assert integration["oncall_integration"]["id"] == "oi1"


def test_match_integration_type():
    integration = {
        "id": "i1",
        "name": "Prometheus Alerts",
        "type": "Prometheus",
    }

    match_integration_type(integration)
    assert integration["oncall_type"] == "alertmanager"


def test_match_integration_type_unsupported():
    integration = {
        "id": "i1",
        "name": "Custom Integration",
        "type": "Custom",
    }

    match_integration_type(integration)
    assert integration.get("oncall_type") is None


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
