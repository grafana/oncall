import typing

from lib.oncall import types as oncall_types
from lib.oncall.api_client import OnCallAPIClient
from lib.splunk import config, types
from lib.utils import find_by_id, transform_wait_delay


def match_escalation_policy(
    policy: types.SplunkEscalationPolicy,
    oncall_escalation_chains: typing.List[oncall_types.OnCallEscalationChain],
) -> None:
    oncall_escalation_chain = None
    for candidate in oncall_escalation_chains:
        if candidate["name"].lower().strip() == policy["name"].lower().strip():
            oncall_escalation_chain = candidate

    policy["oncall_escalation_chain"] = oncall_escalation_chain


def match_users_and_schedules_for_escalation_policy(
    policy: types.SplunkEscalationPolicy,
    users: list[types.SplunkUserWithPagingPolicies],
    schedules: list[types.SplunkScheduleWithTeamAndRotations],
) -> None:
    unmatched_user_ids = set()
    flawed_schedule_team_slugs = set()
    unsupported_escalation_entry_types = set()
    policy_team_slug = policy["slug"]

    def _find_schedule(team_slug: str):
        return find_by_id(schedules, team_slug, "team.slug")

    for step in policy["steps"]:
        for entry in step["entries"]:
            execution_type = entry["executionType"]

            if execution_type in config.UNSUPPORTED_ESCALATION_POLICY_EXECUTION_TYPES:
                unsupported_escalation_entry_types.add(execution_type)
            elif execution_type == "rotation_group":
                if (schedule := _find_schedule(policy_team_slug)) is None:
                    continue
                elif schedule["migration_errors"]:
                    flawed_schedule_team_slugs.add(policy_team_slug)
            elif execution_type == "user":
                target_id = entry["user"]["username"]
                if (user := find_by_id(users, target_id, "username")) is None:
                    continue
                elif not user["oncall_user"]:
                    unmatched_user_ids.add(target_id)

    policy["unsupported_escalation_entry_types"] = list(
        unsupported_escalation_entry_types
    )
    policy["unmatched_users"] = [
        find_by_id(users, user_id, "username") for user_id in unmatched_user_ids
    ]
    policy["flawed_schedules"] = [
        _find_schedule(team_slug) for team_slug in flawed_schedule_team_slugs
    ]


def migrate_escalation_policy(
    escalation_policy: types.SplunkEscalationPolicy,
    users: typing.List[types.SplunkUserWithPagingPolicies],
    schedules: typing.List[types.SplunkScheduleWithTeamAndRotations],
) -> None:
    name = escalation_policy["name"]
    team_slug = escalation_policy["slug"]

    if (
        oncall_escalation_chain := escalation_policy["oncall_escalation_chain"]
    ) is not None:
        OnCallAPIClient.delete(f"escalation_chains/{oncall_escalation_chain['id']}")

    oncall_escalation_chain: oncall_types.OnCallEscalationChain = (
        OnCallAPIClient.create("escalation_chains", {"name": name, "team_id": None})
    )
    oncall_escalation_chain_id = oncall_escalation_chain["id"]

    escalation_policy["oncall_escalation_chain"] = oncall_escalation_chain

    oncall_escalation_policies: typing.List[
        oncall_types.OnCallEscalationPolicyCreatePayload
    ] = []
    for step in escalation_policy["steps"]:
        oncall_escalation_policies.extend(
            transform_step(
                step, team_slug, oncall_escalation_chain_id, users, schedules
            )
        )

    for policy in oncall_escalation_policies:
        OnCallAPIClient.create("escalation_policies", policy)


def transform_step(
    step: types.SplunkEscalationPolicyStep,
    team_slug: str,
    escalation_chain_id: str,
    users: typing.List[types.SplunkUserWithPagingPolicies],
    schedules: typing.List[types.SplunkScheduleWithTeamAndRotations],
) -> typing.List[oncall_types.OnCallEscalationPolicyCreatePayload]:
    escalation_policies: typing.List[
        oncall_types.OnCallEscalationPolicyCreatePayload
    ] = []

    for entry in step["entries"]:
        execution_type = entry["executionType"]

        if execution_type in config.UNSUPPORTED_ESCALATION_POLICY_EXECUTION_TYPES:
            continue
        elif execution_type == "rotation_group":
            schedule = find_by_id(schedules, team_slug, "team.slug")
            if schedule is None:
                continue

            escalation_policies.append(
                {
                    "escalation_chain_id": escalation_chain_id,
                    "type": "notify_on_call_from_schedule",
                    "notify_on_call_from_schedule": schedule["oncall_schedule"]["id"],
                }
            )

            continue
        elif execution_type == "user":
            user = find_by_id(users, entry["user"]["username"], "username")
            if user is None or not user["oncall_user"]:
                continue

            escalation_policies.append(
                {
                    "escalation_chain_id": escalation_chain_id,
                    "type": "notify_persons",
                    "persons_to_notify": [user["oncall_user"]["id"]],
                }
            )

    if (timeout := step["timeout"]) > 0 and escalation_policies:
        escalation_policies.insert(
            0,
            {
                "escalation_chain_id": escalation_chain_id,
                "type": "wait",
                "duration": transform_wait_delay(timeout),
            },
        )

    return escalation_policies
