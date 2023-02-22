from migrator.utils import find_by_id


def match_user(user: dict, oncall_users: list[dict]) -> None:
    oncall_user = None
    for candidate_user in oncall_users:
        if user["email"].lower() == candidate_user["email"].lower():
            oncall_user = candidate_user
            break

    user["oncall_user"] = oncall_user


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
