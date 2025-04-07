from unittest.mock import patch

from lib.opsgenie.resources.integrations import (
    filter_integrations,
    match_integration,
    migrate_integration,
)


@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_TEAM", "team1")
def test_filter_integrations_by_team():
    integrations = [
        {
            "id": "i1",
            "name": "Integration 1",
            "teamId": "team1",
        },
        {
            "id": "i2",
            "name": "Integration 2",
            "teamId": "team2",
        },
        {
            "id": "i3",
            "name": "Integration 3",
            "teamId": "team1",
        },
    ]

    filtered = filter_integrations(integrations)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "i1"
    assert filtered[1]["id"] == "i3"


@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_TEAM", None)
@patch(
    "lib.opsgenie.resources.integrations.OPSGENIE_FILTER_INTEGRATION_REGEX", "^Prod.*"
)
def test_filter_integrations_by_regex():
    integrations = [
        {
            "id": "i1",
            "name": "Production Alert",
            "teamId": "team1",
        },
        {
            "id": "i2",
            "name": "Staging Alert",
            "teamId": "team2",
        },
        {
            "id": "i3",
            "name": "Prod DB Alert",
            "teamId": "team1",
        },
    ]

    filtered = filter_integrations(integrations)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "i1"
    assert filtered[1]["id"] == "i3"


@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_TEAM", "team1")
@patch(
    "lib.opsgenie.resources.integrations.OPSGENIE_FILTER_INTEGRATION_REGEX", "^Prod.*"
)
def test_filter_integrations_by_team_and_regex():
    integrations = [
        {
            "id": "i1",
            "name": "Production Alert",
            "teamId": "team1",
        },
        {
            "id": "i2",
            "name": "Staging Alert",
            "teamId": "team1",
        },
        {
            "id": "i3",
            "name": "Prod DB Alert",
            "teamId": "team2",
        },
        {
            "id": "i4",
            "name": "Prod API Alert",
            "teamId": "team1",
        },
    ]

    filtered = filter_integrations(integrations)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "i1"
    assert filtered[1]["id"] == "i4"


@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_TEAM", None)
@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_INTEGRATION_REGEX", None)
def test_filter_integrations_no_filters():
    integrations = [
        {
            "id": "i1",
            "name": "Integration 1",
            "teamId": "team1",
        },
        {
            "id": "i2",
            "name": "Integration 2",
            "teamId": "team2",
        },
    ]

    filtered = filter_integrations(integrations)
    assert len(filtered) == 2
    assert filtered == integrations


@patch("lib.opsgenie.resources.integrations.OPSGENIE_FILTER_TEAM", "team1")
def test_filter_integrations_missing_team_id():
    integrations = [
        {
            "id": "i1",
            "name": "Integration 1",
            "teamId": "team1",
        },
        {
            "id": "i2",
            "name": "Integration 2",
        },
        {
            "id": "i3",
            "name": "Integration 3",
            "teamId": "team1",
        },
    ]

    filtered = filter_integrations(integrations)
    assert len(filtered) == 2
    assert filtered[0]["id"] == "i1"
    assert filtered[1]["id"] == "i3"


def test_match_integration():
    # supported type
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
    assert integration["oncall_type"] == "alertmanager"

    # unsupported type
    integration = {
        "id": "i1",
        "name": "Custom Integration",
        "type": "Custom",
    }

    match_integration(integration, oncall_integrations)
    assert integration["oncall_integration"] is None
    assert integration.get("oncall_type") is None


@patch("lib.opsgenie.resources.integrations.OnCallAPIClient")
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

    migrate_integration(integration)

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
