from typing import List

from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_TO_ONCALL_VENDOR_MAP,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
)


def match_integration(integration: dict, oncall_integrations: List[dict]) -> None:
    """Match OpsGenie integration with Grafana OnCall integration."""
    oncall_integration = None
    for candidate in oncall_integrations:
        name = integration["name"].lower().strip()
        if name == candidate["name"].lower().strip():
            oncall_integration = candidate

    integration["oncall_integration"] = oncall_integration


def match_integration_type(integration: dict) -> None:
    """Match OpsGenie integration type with Grafana OnCall integration type."""
    integration_type = OPSGENIE_TO_ONCALL_VENDOR_MAP.get(integration["type"])
    if not integration_type and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
        integration_type = "webhook"
    integration["oncall_type"] = integration_type


def match_escalation_policy_for_integration(
    integration: dict, escalation_policies: List[dict]
) -> None:
    """Match escalation policy for integration."""
    if not integration.get("escalation"):
        return

    policy = next(
        (p for p in escalation_policies if p["id"] == integration["escalation"]["id"]),
        None,
    )
    if policy:
        integration["oncall_escalation_chain"] = policy.get("oncall_escalation_chain")


def migrate_integration(integration: dict, escalation_policies: List[dict]) -> None:
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
