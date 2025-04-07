import re
import typing

from lib.common.report import TAB
from lib.oncall.api_client import OnCallAPIClient
from lib.pagerduty.config import (
    PAGERDUTY_FILTER_INTEGRATION_REGEX,
    PAGERDUTY_FILTER_TEAM,
    PAGERDUTY_TO_ONCALL_VENDOR_MAP,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
    VERBOSE_LOGGING,
)
from lib.utils import find_by_id


def filter_integrations(
    integrations: typing.List[typing.Dict[str, typing.Any]],
) -> typing.List[typing.Dict[str, typing.Any]]:
    """
    Filter integrations based on configured filters.

    If multiple filters are specified, an integration only needs to match one of them
    to be included (OR operation between filters).
    """
    if not any([PAGERDUTY_FILTER_TEAM, PAGERDUTY_FILTER_INTEGRATION_REGEX]):
        return integrations  # No filters specified, return all

    filtered_integrations = []
    filtered_out = 0
    filtered_reasons = {}

    for integration in integrations:
        matches_any_filter = False
        reasons = []

        # Filter by team
        if PAGERDUTY_FILTER_TEAM:
            teams = integration["service"].get("teams", [])
            if any(team["summary"] == PAGERDUTY_FILTER_TEAM for team in teams):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No teams found for team filter: {PAGERDUTY_FILTER_TEAM}"
                )

        # Filter by name regex
        if PAGERDUTY_FILTER_INTEGRATION_REGEX:
            integration_name = (
                f"{integration['service']['name']} - {integration['name']}"
            )
            if re.match(PAGERDUTY_FILTER_INTEGRATION_REGEX, integration_name):
                matches_any_filter = True
            else:
                reasons.append(
                    f"Integration regex filter: {PAGERDUTY_FILTER_INTEGRATION_REGEX}"
                )

        if matches_any_filter:
            filtered_integrations.append(integration)
        else:
            filtered_out += 1
            filtered_reasons[integration["id"]] = reasons

    if filtered_out > 0:
        summary = f"Filtered out {filtered_out} integrations"
        print(summary)

        # Only print detailed reasons in verbose mode
        if VERBOSE_LOGGING:
            for integration_id, reasons in filtered_reasons.items():
                print(f"{TAB}Integration {integration_id}: {', '.join(reasons)}")

    return filtered_integrations


def match_integration(integration: dict, oncall_integrations: list[dict]) -> None:
    oncall_integration = None
    for candidate in oncall_integrations:
        name = (
            "{} - {}".format(integration["service"]["name"], integration["name"])
            .lower()
            .strip()
        )
        if candidate["name"].lower().strip() == name:
            oncall_integration = candidate

    integration["oncall_integration"] = oncall_integration


def match_integration_type(integration: dict, vendors: list[dict]) -> None:
    vendors_map = {vendor["id"]: vendor for vendor in vendors}

    if integration["type"] == "generic_email_inbound_integration":
        # ignore vendor name for generic email inbound integrations
        integration["vendor_name"] = None
        integration["oncall_type"] = "inbound_email"
        return

    if integration["vendor"] is None:
        integration["vendor_name"] = None
        if UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
            integration["oncall_type"] = "webhook"
            integration["converted_to_webhook"] = True
        else:
            integration["oncall_type"] = None
        return

    vendor_id = integration["vendor"]["id"]
    vendor_name = vendors_map[vendor_id]["name"]

    integration["vendor_name"] = vendor_name
    integration["oncall_type"] = PAGERDUTY_TO_ONCALL_VENDOR_MAP.get(vendor_name)
    if UNSUPPORTED_INTEGRATION_TO_WEBHOOKS and integration["oncall_type"] is None:
        integration["oncall_type"] = "webhook"
        integration["converted_to_webhook"] = True


def migrate_integration(integration: dict, escalation_policies: list[dict]) -> None:
    escalation_policy = find_by_id(
        escalation_policies, integration["service"]["escalation_policy"]["id"]
    )
    oncall_escalation_chain = escalation_policy["oncall_escalation_chain"]

    if integration["oncall_integration"]:
        OnCallAPIClient.delete(
            "integrations/{}".format(integration["oncall_integration"]["id"])
        )

    oncall_name = "{} - {}".format(integration["service"]["name"], integration["name"])

    create_integration(
        oncall_name,
        integration["oncall_type"],
        oncall_escalation_chain["id"],
    )


def create_integration(
    name: str, integration_type: str, escalation_chain_id: str
) -> None:
    payload = {"name": name, "type": integration_type, "team_id": None}

    integration = OnCallAPIClient.create("integrations", payload)

    routes = OnCallAPIClient.list_all(
        "routes/?integration_id={}".format(integration["id"])
    )
    default_route_id = routes[0]["id"]

    OnCallAPIClient.update(
        f"routes/{default_route_id}", {"escalation_chain_id": escalation_chain_id}
    )
