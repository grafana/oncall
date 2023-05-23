from migrator import oncall_api_client
from migrator.config import EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES
from migrator.utils import find_by_id


def match_ruleset(
    ruleset: dict,
    oncall_integrations: list[dict],
    escalation_policies: list[dict],
    services: list[dict],
    integrations: list[dict],
) -> None:
    # Find existing integration with the same name
    oncall_integration = None
    name = _generate_ruleset_name(ruleset, services, integrations)
    for candidate in oncall_integrations:
        if candidate["name"].lower().strip() == name.lower().strip():
            oncall_integration = candidate
    ruleset["oncall_integration"] = oncall_integration
    ruleset["oncall_name"] = name

    # Find services that use escalation policies that cannot be migrated
    service_ids = [
        r["actions"]["route"]["value"]
        for r in ruleset["rules"]
        if not r["disabled"] and r["actions"]["route"]
    ]
    escalation_policy_ids = []
    for service_id in service_ids:
        service = find_by_id(services, service_id)
        # Sometimes service cannot be found, e.g. when it is deleted but still referenced in ruleset
        if service:
            escalation_policy_ids.append(service["escalation_policy"]["id"])

    flawed_escalation_policies = []
    for escalation_policy_id in escalation_policy_ids:
        escalation_policy = find_by_id(escalation_policies, escalation_policy_id)
        if bool(
            escalation_policy["unmatched_users"]
            or escalation_policy["flawed_schedules"]
        ):
            flawed_escalation_policies.append(escalation_policy)

    ruleset["flawed_escalation_policies"] = flawed_escalation_policies


def migrate_ruleset(
    ruleset: dict, escalation_policies: list[dict], services: list[dict]
) -> None:
    # Delete existing integration with the same name
    if ruleset["oncall_integration"]:
        oncall_api_client.delete(
            "integrations/{}".format(ruleset["oncall_integration"]["id"])
        )

    # Create new integration with type "webhook"
    integration_payload = {
        "name": ruleset["oncall_name"],
        "type": "webhook",
        "team_id": None,
    }
    integration = oncall_api_client.create("integrations", integration_payload)

    # Migrate rules that are not disabled and not catch-all
    rules = [r for r in ruleset["rules"] if not r["disabled"] and not r["catch_all"]]
    for rule in sorted(rules, key=lambda r: r["position"]):
        service_id = (
            rule["actions"]["route"]["value"] if rule["actions"]["route"] else None
        )

        escalation_chain_id = _pd_service_id_to_oncall_escalation_chain_id(
            service_id, services, escalation_policies
        )
        filtering_term = transform_condition_to_jinja(rule["conditions"])
        route_payload = {
            "routing_type": "jinja2",
            "routing_regex": filtering_term,
            "integration_id": integration["id"],
            "escalation_chain_id": escalation_chain_id,
        }
        oncall_api_client.create("routes", route_payload)

    # Migrate catch-all rule
    catch_all_rule = [r for r in ruleset["rules"] if r["catch_all"]][0]
    catch_all_service_id = (
        catch_all_rule["actions"]["route"]["value"]
        if catch_all_rule["actions"]["route"]
        else None
    )
    catch_all_escalation_chain_id = _pd_service_id_to_oncall_escalation_chain_id(
        catch_all_service_id, services, escalation_policies
    )

    if catch_all_escalation_chain_id:
        # Get the default route and update it to use appropriate escalation chain
        routes = oncall_api_client.list_all(
            "routes/?integration_id={}".format(integration["id"])
        )
        default_route_id = routes[-1]["id"]
        oncall_api_client.update(
            f"routes/{default_route_id}",
            {"escalation_chain_id": catch_all_escalation_chain_id},
        )


def transform_condition_to_jinja(condition):
    """
    Transform PD event rule condition to Jinja2 template
    """

    operator = condition["operator"]
    assert operator in ("and", "or")

    # Insert "and" or "or" between subconditions
    template = f" {operator} ".join(
        [
            "(" + transform_subcondition_to_jinja(subcondition) + ")"
            for subcondition in condition["subconditions"]
        ]
    )
    template = "{{ " + template + " }}"
    return template


def transform_subcondition_to_jinja(subcondition):
    """
    Transform PD event rule subcondition to Jinja2 template.
    """
    operator = subcondition["operator"]
    path = subcondition["parameters"]["path"]
    value = subcondition["parameters"]["value"]
    if value:
        value = value.replace('"', '\\"').replace("'", "\\'")

    OPERATOR_TO_JINJA_TEMPLATE = {
        "exists": "{path} is defined",
        "nexists": "{path} is not defined",
        "equals": '{path} == "{value}"',
        "nequals": '{path} != "{value}"',
        "contains": '"{value}" in {path}',
        "ncontains": '"{value}" not in {path}',
        "matches": '{path} | regex_match("{value}")',
        "nmatches": 'not ({path} | regex_match("{value}"))',
    }
    jinja_template = OPERATOR_TO_JINJA_TEMPLATE[operator].format(path=path, value=value)
    return jinja_template


def _pd_service_id_to_oncall_escalation_chain_id(
    service_id, services, escalation_policies
):
    """
    Helper function to get the OnCall escalation chain ID from a PD service ID.
    """

    if service_id is None:
        return None

    service = find_by_id(services, service_id)
    if service is None:
        # Service cannot be found, e.g. when it is deleted but still referenced in ruleset
        return None

    escalation_policy_id = service["escalation_policy"]["id"]
    escalation_policy = find_by_id(escalation_policies, escalation_policy_id)
    escalation_chain_id = escalation_policy["oncall_escalation_chain"]["id"]

    return escalation_chain_id


def _generate_ruleset_name(ruleset, services, integrations):
    result = "{} Ruleset".format(ruleset["name"])
    if not EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES:
        return result

    service_ids = [
        r["actions"]["route"]["value"]
        for r in sorted(ruleset["rules"], key=lambda r: r["position"])
        if not r["disabled"] and r["actions"]["route"]
    ]

    ruleset_services = [find_by_id(services, service_id) for service_id in service_ids]
    ruleset_services = [s for s in ruleset_services if s is not None]
    if not ruleset_services:
        return result

    service_names = []
    for service in ruleset_services:
        service_name = service["name"]
        service_integrations = [
            integration
            for integration in integrations
            if integration["service"]["id"] == service["id"]
        ]
        if service_integrations:
            service_name += " ({})".format(
                ", ".join([integration["name"] for integration in service_integrations])
            )
        service_names.append(service_name)

    # OnCall limit for integration name is 150 chars
    return "{}: {}".format(result, ", ".join(service_names))[:150]
