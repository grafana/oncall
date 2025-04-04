import re
from typing import List

from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.config import (
    OPSGENIE_FILTER_ESCALATION_POLICY_REGEX,
    OPSGENIE_FILTER_TEAM,
)
from lib.utils import transform_wait_delay


def determine_policy_name(policy: dict) -> str:
    """Determine the name of the policy."""
    return f"{policy['ownerTeam']['name']} - {policy['name']}"


def filter_escalation_policies(policies: list[dict]) -> list[dict]:
    """Apply filters to escalation policies."""
    if OPSGENIE_FILTER_TEAM:
        filtered_policies = []
        for p in policies:
            if p["ownerTeam"]["id"] == OPSGENIE_FILTER_TEAM:
                filtered_policies.append(p)
        policies = filtered_policies

    if OPSGENIE_FILTER_ESCALATION_POLICY_REGEX:
        pattern = re.compile(OPSGENIE_FILTER_ESCALATION_POLICY_REGEX)
        policies = [p for p in policies if pattern.match(p["name"])]

    return policies


def match_escalation_policy(policy: dict, oncall_escalation_chains: List[dict]) -> None:
    """
    Match OpsGenie escalation policy with Grafana OnCall escalation chain.
    """
    oncall_chain = None
    for candidate in oncall_escalation_chains:
        if (
            determine_policy_name(policy).lower().strip()
            == candidate["name"].lower().strip()
        ):
            oncall_chain = candidate

    policy["oncall_escalation_chain"] = oncall_chain


def match_users_and_schedules_for_escalation_policy(
    policy: dict, users: List[dict], schedules: List[dict]
) -> None:
    """
    Match users and schedules referenced in escalation policy.
    """
    policy["matched_users"] = []
    policy["matched_schedules"] = []

    for rule in policy["rules"]:
        recipient = rule.get("recipient", {})
        if recipient.get("type") == "user":
            for user in users:
                if user["id"] == recipient.get("id") and user.get("oncall_user"):
                    policy["matched_users"].append(user)
        elif recipient.get("type") == "schedule":
            for schedule in schedules:
                if schedule["id"] == recipient.get("id") and not schedule.get(
                    "migration_errors"
                ):
                    policy["matched_schedules"].append(schedule)


def migrate_escalation_policy(
    policy: dict, users: List[dict], schedules: List[dict]
) -> None:
    """
    Migrate OpsGenie escalation policy to Grafana OnCall.
    """
    if policy["oncall_escalation_chain"]:
        OnCallAPIClient.delete(
            f"escalation_chains/{policy['oncall_escalation_chain']['id']}"
        )

    # Create new escalation chain
    chain_payload = {"name": determine_policy_name(policy), "team_id": None}
    chain = OnCallAPIClient.create("escalation_chains", chain_payload)
    policy["oncall_escalation_chain"] = chain

    # Create escalation policies for each rule
    position = 0
    for rule in policy["rules"]:
        if rule.get("notifyType") != "default":
            continue

        # Convert wait duration from minutes to seconds + add wait step if there's a delay
        delay = rule.get("delay", {}).get("timeAmount")
        if delay:
            wait_payload = {
                "escalation_chain_id": chain["id"],
                "position": position,
                "type": "wait",
                "duration": transform_wait_delay(delay),
            }
            OnCallAPIClient.create("escalation_policies", wait_payload)
            position += 1

        # Create notification step
        recipient = rule["recipient"]
        if recipient["type"] == "user":
            user = next((u for u in users if u["id"] == recipient["id"]), None)
            if user and user.get("oncall_user"):
                policy_payload = {
                    "escalation_chain_id": chain["id"],
                    "position": position,
                    "type": "notify_persons",
                    "persons_to_notify": [user["oncall_user"]["id"]],
                    "important": False,
                }
                OnCallAPIClient.create("escalation_policies", policy_payload)
                position += 1

        elif recipient["type"] == "schedule":
            schedule = next((s for s in schedules if s["id"] == recipient["id"]), None)
            if schedule and schedule.get("oncall_schedule"):
                policy_payload = {
                    "escalation_chain_id": chain["id"],
                    "position": position,
                    "type": "notify_on_call_from_schedule",
                    "notify_on_call_from_schedule": schedule["oncall_schedule"]["id"],
                    "important": False,
                }
                OnCallAPIClient.create("escalation_policies", policy_payload)
                position += 1
