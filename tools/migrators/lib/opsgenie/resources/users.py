from typing import List


def match_users_for_schedule(schedule: dict, users: List[dict]) -> None:
    """Match users referenced in schedule."""
    schedule["matched_users"] = []

    for rotation in schedule["rotations"]:
        for participant in rotation["participants"]:
            if participant["type"] == "user":
                for user in users:
                    if user["id"] == participant["id"] and user.get("oncall_user"):
                        schedule["matched_users"].append(user)


def match_users_and_schedules_for_escalation_policy(
    policy: dict, users: List[dict], schedules: List[dict]
) -> None:
    """Match users and schedules referenced in escalation policy."""
    policy["matched_users"] = []
    policy["matched_schedules"] = []

    for rule in policy["rules"]:
        for recipient in rule["recipients"]:
            if recipient["type"] == "user":
                for user in users:
                    if user["id"] == recipient["id"] and user.get("oncall_user"):
                        policy["matched_users"].append(user)
            elif recipient["type"] == "schedule":
                for schedule in schedules:
                    if schedule["id"] == recipient["id"] and not schedule.get("migration_errors"):
                        policy["matched_schedules"].append(schedule)
