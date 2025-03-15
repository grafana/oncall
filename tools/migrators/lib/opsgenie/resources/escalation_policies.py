from typing import List

from lib.oncall.api_client import OnCallAPIClient
from lib.utils import transform_wait_delay


def match_escalation_policy(policy: dict, oncall_escalation_chains: List[dict]) -> None:
    """Match OpsGenie escalation policy with Grafana OnCall escalation chain."""
    oncall_chain = None
    for candidate in oncall_escalation_chains:
        if policy["name"].lower().strip() == candidate["name"].lower().strip():
            oncall_chain = candidate

    policy["oncall_escalation_chain"] = oncall_chain


def match_escalation_policy_for_integration(integration: dict, policies: List[dict]) -> None:
    """Match OpsGenie integration with its escalation policy."""
    integration["matched_escalation_policy"] = None

    # First try to match by ID if the integration has a policy ID
    if integration.get("escalationPolicyId"):
        for policy in policies:
            if policy["id"] == integration["escalationPolicyId"]:
                integration["matched_escalation_policy"] = policy
                return

    # If no match by ID, try to match by name
    # Some integrations might reference the policy by name instead of ID
    if integration.get("escalationPolicyName"):
        for policy in policies:
            if policy["name"].lower().strip() == integration["escalationPolicyName"].lower().strip():
                integration["matched_escalation_policy"] = policy
                return


def migrate_escalation_policy(
    policy: dict, users: List[dict], schedules: List[dict]
) -> None:
    """Migrate OpsGenie escalation policy to Grafana OnCall."""
    if policy["oncall_escalation_chain"]:
        OnCallAPIClient.delete(
            f"escalation_chains/{policy['oncall_escalation_chain']['id']}"
        )

    # Create new escalation chain
    chain_payload = {"name": policy["name"], "team_id": None}
    chain = OnCallAPIClient.create("escalation_chains", chain_payload)
    policy["oncall_escalation_chain"] = chain

    # Create escalation policies for each rule
    position = 0
    for rule in policy["rules"]:
        # Convert wait duration from minutes to seconds
        wait_delay = transform_wait_delay(rule.get("notifyOnce", False), rule.get("delay", 0))

        # Create policies for each recipient
        for recipient in rule["recipients"]:
            if recipient["type"] == "user":
                user = next(
                    (u for u in users if u["id"] == recipient["id"]), None
                )
                if user and user.get("oncall_user"):
                    policy_payload = {
                        "escalation_chain_id": chain["id"],
                        "position": position,
                        "type": "notify_persons",
                        "persons_to_notify": [user["oncall_user"]["id"]],
                        "important": rule.get("isHighPriority", False),
                    }
                    OnCallAPIClient.create("escalation_policies", policy_payload)
                    position += 1

            elif recipient["type"] == "schedule":
                schedule = next(
                    (s for s in schedules if s["id"] == recipient["id"]), None
                )
                if schedule and schedule.get("oncall_schedule"):
                    policy_payload = {
                        "escalation_chain_id": chain["id"],
                        "position": position,
                        "type": "notify_on_call_from_schedule",
                        "schedule_id": schedule["oncall_schedule"]["id"],
                        "important": rule.get("isHighPriority", False),
                    }
                    OnCallAPIClient.create("escalation_policies", policy_payload)
                    position += 1

        # Add wait step if there's a delay
        if wait_delay:
            wait_payload = {
                "escalation_chain_id": chain["id"],
                "position": position,
                "type": "wait",
                "duration": wait_delay,
            }
            OnCallAPIClient.create("escalation_policies", wait_payload)
            position += 1
