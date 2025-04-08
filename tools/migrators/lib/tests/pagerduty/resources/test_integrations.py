from unittest.mock import patch

import pytest

from lib.pagerduty.resources.integrations import filter_integrations, match_integration


@pytest.fixture
def mock_integration():
    return {
        "id": "INTEGRATION1",
        "name": "Test Integration",
        "service": {
            "name": "Service 1",
            "teams": [{"summary": "Team 1"}],
        },
    }


@patch("lib.pagerduty.resources.integrations.PAGERDUTY_FILTER_TEAM", "Team 1")
def test_filter_integrations_by_team(mock_integration):
    integrations = [
        mock_integration,
        {
            **mock_integration,
            "service": {
                "name": "Service 1",
                "teams": [{"summary": "Team 2"}],
            },
        },
    ]
    filtered = filter_integrations(integrations)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "INTEGRATION1"


@patch(
    "lib.pagerduty.resources.integrations.PAGERDUTY_FILTER_INTEGRATION_REGEX",
    "^Service 1 - Test",
)
def test_filter_integrations_by_regex(mock_integration):
    integrations = [
        mock_integration,
        {
            **mock_integration,
            "service": {"name": "Service 2", "teams": [{"summary": "Team 1"}]},
        },
    ]
    filtered = filter_integrations(integrations)
    assert len(filtered) == 1
    assert filtered[0]["id"] == "INTEGRATION1"


@patch("lib.pagerduty.resources.integrations.PAGERDUTY_FILTER_TEAM", "Team 1")
@patch(
    "lib.pagerduty.resources.integrations.PAGERDUTY_FILTER_INTEGRATION_REGEX",
    "^Service 2 - Test",
)
def test_filter_integrations_with_multiple_filters_or_logic(mock_integration):
    """Test that OR logic is applied between filters - an integration matching any filter is included"""
    integrations = [
        mock_integration,  # Has Team 1 but doesn't match regex
        {
            "id": "INTEGRATION2",
            "name": "Test Integration",
            "service": {
                "name": "Service 2",  # Matches regex
                "teams": [{"summary": "Team 2"}],  # Not Team 1
            },
        },
        {
            "id": "INTEGRATION3",
            "name": "Test Integration",
            "service": {
                "name": "Service 3",  # Doesn't match regex
                "teams": [{"summary": "Team 3"}],  # Not Team 1
            },
        },
    ]
    filtered = filter_integrations(integrations)
    # INTEGRATION1 matches team filter, INTEGRATION2 matches regex filter, INTEGRATION3 matches neither
    assert len(filtered) == 2
    assert {i["id"] for i in filtered} == {"INTEGRATION1", "INTEGRATION2"}


def test_match_integration_name_case_insensitive():
    pd_integration = {"service": {"name": "Test service"}, "name": "test Integration"}
    oncall_integrations = [{"name": "test Service - Test integration"}]

    match_integration(pd_integration, oncall_integrations)
    assert pd_integration["oncall_integration"] == oncall_integrations[0]


def test_match_integration_name_extra_spaces():
    pd_integration = {
        "service": {"name": " test service "},
        "name": " test integration ",
    }
    oncall_integrations = [{"name": "test service  -  test integration"}]

    match_integration(pd_integration, oncall_integrations)
    assert pd_integration["oncall_integration"] == oncall_integrations[0]
