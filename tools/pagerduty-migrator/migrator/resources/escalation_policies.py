from migrator import oncall_api_client
from migrator.utils import find_by_id, transform_wait_delay


def match_escalation_policy(policy: dict, oncall_escalation_chains: list[dict]) -> None:
    oncall_escalation_chain = None
    for candidate in oncall_escalation_chains:
        if candidate["name"].lower().strip() == policy["name"].lower().strip():
            oncall_escalation_chain = candidate

    policy["oncall_escalation_chain"] = oncall_escalation_chain


def match_escalation_policy_for_integration(
    integration: dict, escalation_policies: list[dict]
) -> None:
    policy_id = integration["service"]["escalation_policy"]["id"]
    policy = find_by_id(escalation_policies, policy_id)

    integration["is_escalation_policy_flawed"] = bool(
        policy["unmatched_users"] or policy["flawed_schedules"]
    )


def migrate_escalation_policy(
    escalation_policy: dict, users: list[dict], schedules: list[dict]
) -> None:
    name = escalation_policy["name"]
    rules = escalation_policy["escalation_rules"]
    num_loops = escalation_policy["num_loops"]

    if escalation_policy["oncall_escalation_chain"]:
        oncall_api_client.delete(
            "escalation_chains/{}".format(
                escalation_policy["oncall_escalation_chain"]["id"]
            )
        )

    oncall_escalation_chain_payload = {"name": name, "team_id": None}
    oncall_escalation_chain = oncall_api_client.create(
        "escalation_chains", oncall_escalation_chain_payload
    )

    escalation_policy["oncall_escalation_chain"] = oncall_escalation_chain

    oncall_escalation_policies = transform_rules(
        rules, oncall_escalation_chain["id"], users, schedules, num_loops
    )
    for policy in oncall_escalation_policies:
        oncall_api_client.create("escalation_policies", policy)


def transform_rules(
    rules: list[dict],
    escalation_chain_id: str,
    users: list[dict],
    schedules: list[dict],
    num_loops: int,
) -> list[dict]:
    """
    Transform PagerDuty escalation policy rules to Grafana OnCall escalation policies.
    """
    escalation_policies = []
    for rule in rules:
        escalation_policies += transform_rule(
            rule, escalation_chain_id, users, schedules
        )

    if num_loops > 0:
        escalation_policies.append(
            {"escalation_chain_id": escalation_chain_id, "type": "repeat_escalation"}
        )

    return escalation_policies


def transform_rule(
    rule: dict, escalation_chain_id: str, users: list[dict], schedules: list[dict]
) -> list[dict]:
    targets = rule["targets"]
    delay = rule["escalation_delay_in_minutes"]

    schedule_targets = [
        target for target in targets if target["type"] == "schedule_reference"
    ]
    user_targets = [target for target in targets if target["type"] == "user_reference"]

    escalation_policies = []

    for target in schedule_targets:
        schedule = find_by_id(schedules, target["id"])
        if schedule is None:
            continue

        oncall_schedule_id = schedule["oncall_schedule"]["id"]

        escalation_policy = {
            "escalation_chain_id": escalation_chain_id,
            "type": "notify_on_call_from_schedule",
            "notify_on_call_from_schedule": oncall_schedule_id,
        }
        escalation_policies.append(escalation_policy)

    if user_targets:
        rule_users = [find_by_id(users, target["id"]) for target in user_targets]
        oncall_user_ids = [
            user["oncall_user"]["id"]
            for user in rule_users
            if user and user["oncall_user"]
        ]

        user_escalation_policy = {
            "escalation_chain_id": escalation_chain_id,
            "type": "notify_persons",
            "persons_to_notify": oncall_user_ids,
        }
        escalation_policies.append(user_escalation_policy)

    if delay > 0:
        wait_escalation_policy = {
            "escalation_chain_id": escalation_chain_id,
            "type": "wait",
            "duration": transform_wait_delay(delay),
        }
        escalation_policies.append(wait_escalation_policy)

    return escalation_policies
