from unittest.mock import patch

import pytest

from lib.pagerduty.resources.escalation_policies import (
    filter_escalation_policies,
    match_escalation_policy,
)


@pytest.fixture
def mock_escalation_policy():
    return {
        "id": "POLICY1",
        "name": "Test Policy",
        "teams": [{"summary": "Team 1"}],
        "escalation_rules": [
            {
                "targets": [
                    {"type": "user", "id": "USER1"},
                    {"type": "user", "id": "USER2"},
                ],
            },
        ],
    }


@patch("lib.pagerduty.resources.escalation_policies.PAGERDUTY_FILTER_TEAM", "Team 1")
def test_filter_escalation_policies_by_team(mock_escalation_policy):
    policies = [
        mock_escalation_policy,
        {**mock_escalation_policy, "teams": [{"summary": "Team 2"}]},
    ]
    filtered = filter_escalation_policies(policies)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "POLICY1"


@patch("lib.pagerduty.resources.escalation_policies.PAGERDUTY_FILTER_USERS", ["USER1"])
def test_filter_escalation_policies_by_users(mock_escalation_policy):
    policies = [
        mock_escalation_policy,
        {
            **mock_escalation_policy,
            "escalation_rules": [
                {
                    "targets": [
                        {"type": "user", "id": "USER3"},
                        {"type": "user", "id": "USER4"},
                    ]
                }
            ],
        },
    ]
    filtered = filter_escalation_policies(policies)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "POLICY1"


@patch(
    "lib.pagerduty.resources.escalation_policies.PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX",
    "^Test",
)
def test_filter_escalation_policies_by_regex(mock_escalation_policy):
    policies = [
        mock_escalation_policy,
        {**mock_escalation_policy, "name": "Another Policy"},
    ]
    filtered = filter_escalation_policies(policies)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "POLICY1"


@patch("lib.pagerduty.resources.escalation_policies.PAGERDUTY_FILTER_TEAM", "Team 1")
@patch("lib.pagerduty.resources.escalation_policies.PAGERDUTY_FILTER_USERS", ["USER3"])
def test_filter_escalation_policies_with_multiple_filters_or_logic(
    mock_escalation_policy,
):
    """Test that OR logic is applied between filters - a policy matching any filter is included"""
    policies = [
        mock_escalation_policy,  # Has Team 1 but not USER3
        {
            "id": "POLICY2",
            "name": "Test Policy 2",
            "teams": [{"summary": "Team 2"}],  # Not Team 1
            "escalation_rules": [
                {
                    "targets": [
                        {"type": "user", "id": "USER3"},  # Has USER3
                    ]
                }
            ],
        },
        {
            "id": "POLICY3",
            "name": "Test Policy 3",
            "teams": [{"summary": "Team 3"}],  # Not Team 1
            "escalation_rules": [
                {
                    "targets": [
                        {"type": "user", "id": "USER4"},  # Not USER3
                    ]
                }
            ],
        },
    ]
    filtered = filter_escalation_policies(policies)
    # POLICY1 matches team filter, POLICY2 matches user filter, POLICY3 matches neither
    assert len(filtered) == 2
    assert {p["id"] for p in filtered} == {"POLICY1", "POLICY2"}


def test_match_escalation_policy_name_case_insensitive():
    pd_escalation_policy = {"name": "Test"}
    oncall_escalation_chains = [{"name": "test"}]

    match_escalation_policy(pd_escalation_policy, oncall_escalation_chains)
    assert (
        pd_escalation_policy["oncall_escalation_chain"] == oncall_escalation_chains[0]
    )


def test_match_escalation_policy_name_extra_spaces():
    pd_escalation_policy = {"name": " test "}
    oncall_escalation_chains = [{"name": "test"}]

    match_escalation_policy(pd_escalation_policy, oncall_escalation_chains)
    assert (
        pd_escalation_policy["oncall_escalation_chain"] == oncall_escalation_chains[0]
    )
