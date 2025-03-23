from unittest.mock import patch

from lib.opsgenie.resources.integrations import match_integration, migrate_integration


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
