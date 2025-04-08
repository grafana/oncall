import re
from typing import List

from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_FILTER_INTEGRATION_REGEX,
    OPSGENIE_FILTER_TEAM,
    OPSGENIE_TO_ONCALL_VENDOR_MAP,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
)


def filter_integrations(integrations: list[dict]) -> list[dict]:
    """Apply filters to integrations."""
    if OPSGENIE_FILTER_TEAM:
        integrations = [
            i for i in integrations if i.get("teamId") == OPSGENIE_FILTER_TEAM
        ]

    if OPSGENIE_FILTER_INTEGRATION_REGEX:
        pattern = re.compile(OPSGENIE_FILTER_INTEGRATION_REGEX)
        integrations = [i for i in integrations if pattern.match(i["name"])]

    return integrations


def match_integration(integration: dict, oncall_integrations: List[dict]) -> None:
    """
    Match OpsGenie integration with Grafana OnCall integration + match opsgenie
    integration type with Grafana OnCall integration type.
    """
    oncall_integration = None
    for candidate in oncall_integrations:
        name = integration["name"].lower().strip()
        if name == candidate["name"].lower().strip():
            oncall_integration = candidate

    integration["oncall_integration"] = oncall_integration

    integration_type = OPSGENIE_TO_ONCALL_VENDOR_MAP.get(integration["type"])
    if not integration_type and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
        integration_type = "webhook"
    integration["oncall_type"] = integration_type


def migrate_integration(integration: dict) -> None:
    """Migrate OpsGenie integration to Grafana OnCall."""
    if integration["oncall_integration"]:
        OnCallAPIClient.delete(
            f"integrations/{integration['oncall_integration']['id']}"
        )

    # Create new integration
    payload = {
        "name": integration["name"],
        "type": integration["oncall_type"],
        "team_id": None,
    }

    if integration.get("oncall_escalation_chain"):
        payload["escalation_chain_id"] = integration["oncall_escalation_chain"]["id"]

    integration["oncall_integration"] = OnCallAPIClient.create("integrations", payload)
