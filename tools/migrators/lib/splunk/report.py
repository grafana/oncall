import typing

from lib.common.report import ERROR_SIGN, SUCCESS_SIGN, TAB, WARNING_SIGN
from lib.splunk import types


def format_user(user: types.SplunkUserWithPagingPolicies) -> str:
    result = f"{user['firstName']} {user['lastName']} ({user['email']})"

    if user["oncall_user"]:
        result = f"{SUCCESS_SIGN} {result}"
    else:
        result = f"{ERROR_SIGN} {result} — no Grafana OnCall user found with this email"
    return result


def format_team(team: types.SplunkTeam) -> str:
    return f"{SUCCESS_SIGN} {team['name']} ({team['slug']})"


def format_schedule(schedule: types.SplunkScheduleWithTeamAndRotations) -> str:
    schedule_name = schedule["name"]
    if schedule["migration_errors"]:
        result = f"{ERROR_SIGN} {schedule_name} — some layers cannot be migrated"
    else:
        result = f"{SUCCESS_SIGN} {schedule_name}"
    return result


def format_escalation_policy(policy: types.SplunkEscalationPolicy) -> str:
    policy_name = policy["name"]
    unmatched_users = policy["unmatched_users"]
    flawed_schedules = policy["flawed_schedules"]

    if unmatched_users and flawed_schedules:
        result = f"{ERROR_SIGN} {policy_name} — policy references unmatched users and schedules that cannot be migrated"
    elif unmatched_users:
        result = f"{ERROR_SIGN} {policy_name} — policy references unmatched users"
    elif flawed_schedules:
        result = f"{ERROR_SIGN} {policy_name} — policy references schedules that cannot be migrated"
    else:
        result = f"{SUCCESS_SIGN} {policy_name}"

    return result


def user_report(users: typing.List[types.SplunkUserWithPagingPolicies]) -> str:
    result = "User notification rules report:"

    for user in sorted(users, key=lambda u: bool(u["oncall_user"]), reverse=True):
        result += f"\n{TAB}{format_user(user)}"

        if user["oncall_user"] and user["pagingPolicies"]:
            result += " (existing notification rules will be deleted)"

    return result


def schedule_report(schedules: list[types.SplunkScheduleWithTeamAndRotations]) -> str:
    result = "Schedule report:"

    for schedule in sorted(schedules, key=lambda s: s["migration_errors"]):
        result += "\n" + TAB + format_schedule(schedule)

        if schedule["oncall_schedule"] and not schedule["migration_errors"]:
            result += " (existing schedule with name '{}' will be deleted)".format(
                schedule["oncall_schedule"]["name"]
            )

        for error in schedule["migration_errors"]:
            result += "\n" + TAB * 2 + "{} {}".format(ERROR_SIGN, error)

    return result


def escalation_policy_report(policies: list[types.SplunkEscalationPolicy]) -> str:
    result = "Escalation policy report: "

    for policy in sorted(
        policies, key=lambda p: bool(p["unmatched_users"] or p["flawed_schedules"])
    ):
        unmatched_users = policy["unmatched_users"]
        flawed_schedules = policy["flawed_schedules"]
        unsupported_escalation_entry_types = policy[
            "unsupported_escalation_entry_types"
        ]
        result += f"\n{TAB}{format_escalation_policy(policy)}"

        if (
            not unmatched_users
            and not flawed_schedules
            and policy["oncall_escalation_chain"]
        ):
            result += f" (existing escalation chain with name '{policy['oncall_escalation_chain']['name']}' will be deleted)"

        for user in unmatched_users:
            result += f"\n{TAB * 2}{format_user(user)}"

        for schedule in policy["flawed_schedules"]:
            result += f"\n{TAB * 2}{format_schedule(schedule)}"

        for entry_type in unsupported_escalation_entry_types:
            result += f"\n{TAB * 2}{WARNING_SIGN} unsupported escalation entry type: {entry_type}"

    return result
