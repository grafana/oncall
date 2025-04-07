import typing

from lib.common.report import TAB
from lib.pagerduty.config import PAGERDUTY_FILTER_USERS, VERBOSE_LOGGING
from lib.utils import find_by_id


def filter_users(
    users: typing.List[typing.Dict[str, typing.Any]]
) -> typing.List[typing.Dict[str, typing.Any]]:
    """
    Filter users based on PAGERDUTY_FILTER_USERS.

    When PAGERDUTY_FILTER_USERS is set, only users with IDs in that list will be included.
    """
    if not PAGERDUTY_FILTER_USERS:
        return users  # No filtering, return all users

    filtered_users = []
    filtered_out = 0

    for user in users:
        if user["id"] in PAGERDUTY_FILTER_USERS:
            filtered_users.append(user)
        else:
            filtered_out += 1

    if filtered_out > 0:
        summary = f"Filtered out {filtered_out} users (keeping only users specified in PAGERDUTY_FILTER_USERS)"
        print(summary)

        # Only print detailed info in verbose mode
        if VERBOSE_LOGGING:
            print(
                f"{TAB}Keeping only users with IDs: {', '.join(PAGERDUTY_FILTER_USERS)}"
            )

    return filtered_users


def match_users_for_schedule(schedule: dict, users: list[dict]) -> None:
    unmatched_users = []

    for user_reference in schedule["users"]:
        user = find_by_id(users, user_reference["id"])

        if not user:
            continue

        if not user["oncall_user"]:
            unmatched_users.append(user)

    schedule["unmatched_users"] = unmatched_users


def match_users_and_schedules_for_escalation_policy(
    policy: dict, users: list[dict], schedules: list[dict]
) -> None:
    unmatched_user_ids = set()
    flawed_schedule_ids = set()

    for rule in policy["escalation_rules"]:
        targets = rule["targets"]

        for target in targets:
            target_id = target["id"]

            if target["type"] == "user_reference":
                user = find_by_id(users, target_id)

                if not user:
                    continue

                if not user["oncall_user"]:
                    unmatched_user_ids.add(target_id)

            elif target["type"] == "schedule_reference":
                schedule = find_by_id(schedules, target_id)

                if not schedule:
                    continue

                if schedule["unmatched_users"] or schedule["migration_errors"]:
                    flawed_schedule_ids.add(target_id)

    policy["unmatched_users"] = [
        find_by_id(users, user_id) for user_id in unmatched_user_ids
    ]
    policy["flawed_schedules"] = [
        find_by_id(schedules, schedule_id) for schedule_id in flawed_schedule_ids
    ]
