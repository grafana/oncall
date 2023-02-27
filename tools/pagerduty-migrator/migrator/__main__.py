from pdpyras import APISession

from migrator import oncall_api_client
from migrator.config import MODE, MODE_PLAN, PAGERDUTY_API_TOKEN
from migrator.report import (
    TAB,
    escalation_policy_report,
    format_escalation_policy,
    format_integration,
    format_schedule,
    format_user,
    integration_report,
    schedule_report,
    user_report,
)
from migrator.resources.escalation_policies import (
    match_escalation_policy,
    match_escalation_policy_for_integration,
    migrate_escalation_policy,
)
from migrator.resources.integrations import (
    match_integration,
    match_integration_type,
    migrate_integration,
)
from migrator.resources.notification_rules import migrate_notification_rules
from migrator.resources.schedules import match_schedule, migrate_schedule
from migrator.resources.users import (
    match_user,
    match_users_and_schedules_for_escalation_policy,
    match_users_for_schedule,
)


def main() -> None:
    session = APISession(PAGERDUTY_API_TOKEN)
    session.timeout = 20

    print("▶ Fetching users...")
    users = session.list_all("users", params={"include[]": "notification_rules"})

    oncall_users = oncall_api_client.list_all("users")
    oncall_notification_rules = oncall_api_client.list_all(
        "personal_notification_rules/?important=false"
    )
    for user in oncall_users:
        user["notification_rules"] = [
            rule for rule in oncall_notification_rules if rule["user_id"] == user["id"]
        ]

    print("▶ Fetching schedules...")
    schedules = session.list_all(
        "schedules", params={"include[]": "schedule_layers", "time_zone": "UTC"}
    )
    oncall_schedules = oncall_api_client.list_all("schedules")

    print("▶ Fetching escalation policies...")
    escalation_policies = session.list_all("escalation_policies")
    oncall_escalation_chains = oncall_api_client.list_all("escalation_chains")

    print("▶ Fetching integrations...")
    services = session.list_all("services", params={"include[]": "integrations"})
    vendors = session.list_all("vendors")

    integrations = []
    for service in services:
        service_integrations = service.pop("integrations")
        for integration in service_integrations:
            integration["service"] = service
            integrations.append(integration)

    oncall_integrations = oncall_api_client.list_all("integrations")

    for user in users:
        match_user(user, oncall_users)

    user_id_map = {
        u["id"]: u["oncall_user"]["id"] if u["oncall_user"] else None for u in users
    }

    for schedule in schedules:
        match_schedule(schedule, oncall_schedules, user_id_map)
        match_users_for_schedule(schedule, users)

    for policy in escalation_policies:
        match_escalation_policy(policy, oncall_escalation_chains)
        match_users_and_schedules_for_escalation_policy(policy, users, schedules)

    for integration in integrations:
        match_integration(integration, oncall_integrations)
        match_integration_type(integration, vendors)
        match_escalation_policy_for_integration(integration, escalation_policies)

    if MODE == MODE_PLAN:
        print()
        print(user_report(users))
        print()
        print(schedule_report(schedules))
        print()
        print(escalation_policy_report(escalation_policies))
        print()
        print(integration_report(integrations))

        return

    print("▶ Migrating user notification rules...")
    for user in users:
        if user["oncall_user"]:
            migrate_notification_rules(user)
            print(TAB + format_user(user))

    print("▶ Migrating schedules...")
    for schedule in schedules:
        if not schedule["unmatched_users"] and not schedule["migration_errors"]:
            migrate_schedule(schedule, user_id_map)
            print(TAB + format_schedule(schedule))

    print("▶ Migrating escalation policies...")
    for policy in escalation_policies:
        if not policy["unmatched_users"] and not policy["flawed_schedules"]:
            migrate_escalation_policy(policy, users, schedules)
            print(TAB + format_escalation_policy(policy))

    print("▶ Migrating integrations...")
    for integration in integrations:
        if (
            integration["oncall_type"]
            and not integration["is_escalation_policy_flawed"]
        ):
            migrate_integration(integration, escalation_policies)
            print(TAB + format_integration(integration))


if __name__ == "__main__":
    main()
