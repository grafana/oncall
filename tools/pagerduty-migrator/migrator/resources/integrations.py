from migrator import oncall_api_client
from migrator.config import PAGERDUTY_TO_ONCALL_VENDOR_MAP
from migrator.utils import find_by_id


def match_integration(integration: dict, oncall_integrations: list[dict]) -> None:
    oncall_integration = None
    for candidate in oncall_integrations:
        if candidate["name"] == "{} - {}".format(
            integration["service"]["name"], integration["name"]
        ):
            oncall_integration = candidate

    integration["oncall_integration"] = oncall_integration


def match_integration_type(integration: dict, vendors: list[dict]) -> None:
    vendors_map = {vendor["id"]: vendor for vendor in vendors}

    if (
        integration["type"]
        not in [
            "generic_events_api_inbound_integration",
            "events_api_v2_inbound_integration",
        ]
        or integration["vendor"] is None
    ):
        integration["oncall_type"] = None
        return

    vendor_id = integration["vendor"]["id"]
    vendor_name = vendors_map[vendor_id]["name"]

    integration["oncall_type"] = PAGERDUTY_TO_ONCALL_VENDOR_MAP.get(vendor_name)


def migrate_integration(integration: dict, escalation_policies: list[dict]) -> None:
    escalation_policy = find_by_id(
        escalation_policies, integration["service"]["escalation_policy"]["id"]
    )
    oncall_escalation_chain = escalation_policy["oncall_escalation_chain"]

    if integration["oncall_integration"]:
        oncall_api_client.delete(
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

    integration = oncall_api_client.create("integrations", payload)

    routes = oncall_api_client.list_all(
        "routes/?integration_id={}".format(integration["id"])
    )
    default_route_id = routes[0]["id"]

    oncall_api_client.update(
        f"routes/{default_route_id}", {"escalation_chain_id": escalation_chain_id}
    )
