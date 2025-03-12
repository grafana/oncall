from lib.common.report import TAB
from lib.common.resources.users import match_user
from lib.oncall.api_client import OnCallAPIClient
from lib.opsgenie.api_client import OpsGenieAPIClient
from lib.opsgenie.config import (
    MODE,
    MODE_PLAN,
    OPSGENIE_FILTER_ESCALATION_POLICY_REGEX,
    OPSGENIE_FILTER_INTEGRATION_REGEX,
    OPSGENIE_FILTER_SCHEDULE_REGEX,
    OPSGENIE_FILTER_TEAM,
    OPSGENIE_FILTER_USERS,
    MIGRATE_USERS,
)
from lib.opsgenie.report import (
    escalation_policy_report,
    format_escalation_policy,
    format_integration,
    format_schedule,
    format_user,
    integration_report,
    schedule_report,
    user_report,
)
from lib.opsgenie.resources.escalation_policies import (
    match_escalation_policy,
    match_escalation_policy_for_integration,
    migrate_escalation_policy,
)
from lib.opsgenie.resources.integrations import (
    match_integration,
    match_integration_type,
    migrate_integration,
)
from lib.opsgenie.resources.notification_rules import migrate_notification_rules
from lib.opsgenie.resources.schedules import match_schedule, migrate_schedule
from lib.opsgenie.resources.users import (
    match_users_and_schedules_for_escalation_policy,
    match_users_for_schedule,
)


def filter_schedules(schedules: list[dict]) -> list[dict]:
    """Apply filters to schedules."""
    if OPSGENIE_FILTER_TEAM:
        schedules = [
            s for s in schedules if s["ownerTeam"]["name"] == OPSGENIE_FILTER_TEAM
        ]

    if OPSGENIE_FILTER_SCHEDULE_REGEX:
        import re

        pattern = re.compile(OPSGENIE_FILTER_SCHEDULE_REGEX)
        schedules = [s for s in schedules if pattern.match(s["name"])]

    return schedules


def filter_escalation_policies(policies: list[dict]) -> list[dict]:
    """Apply filters to escalation policies."""
    if OPSGENIE_FILTER_TEAM:
        policies = [
            p for p in policies if p["ownerTeam"]["name"] == OPSGENIE_FILTER_TEAM
        ]

    if OPSGENIE_FILTER_ESCALATION_POLICY_REGEX:
        import re

        pattern = re.compile(OPSGENIE_FILTER_ESCALATION_POLICY_REGEX)
        policies = [p for p in policies if pattern.match(p["name"])]

    return policies


def filter_integrations(integrations: list[dict]) -> list[dict]:
    """Apply filters to integrations."""
    if OPSGENIE_FILTER_TEAM:
        integrations = [
            i for i in integrations if i["ownerTeam"]["name"] == OPSGENIE_FILTER_TEAM
        ]

    if OPSGENIE_FILTER_INTEGRATION_REGEX:
        import re

        pattern = re.compile(OPSGENIE_FILTER_INTEGRATION_REGEX)
        integrations = [i for i in integrations if pattern.match(i["name"])]

    return integrations


def migrate() -> None:
    client = OpsGenieAPIClient()

    if MIGRATE_USERS:
        print("▶ Fetching users...")
        users = client.list_users()
    else:
        print("▶ Skipping user migration as MIGRATE_USERS is false...")
        users = []

    oncall_users = OnCallAPIClient.list_users_with_notification_rules()

    print("▶ Fetching schedules...")
    schedules = client.list_schedules()
    schedules = filter_schedules(schedules)
    oncall_schedules = OnCallAPIClient.list_all("schedules")

    print("▶ Fetching escalation policies...")
    escalation_policies = client.list_escalation_policies()
    escalation_policies = filter_escalation_policies(escalation_policies)
    oncall_escalation_chains = OnCallAPIClient.list_all("escalation_chains")

    print("▶ Fetching integrations...")
    integrations = client.list_integrations()
    integrations = filter_integrations(integrations)
    oncall_integrations = OnCallAPIClient.list_all("integrations")

    # Match users with their Grafana OnCall counterparts
    if MIGRATE_USERS:
        print("\n▶ Matching users...")
        for user in users:
            match_user(user, oncall_users)
        print(user_report(users))

    # Match schedules with their Grafana OnCall counterparts
    print("\n▶ Matching schedules...")
    user_id_map = {u["id"]: u["oncall_user"]["id"] for u in users if u.get("oncall_user")}
    for schedule in schedules:
        match_schedule(schedule, oncall_schedules, user_id_map)
        match_users_for_schedule(schedule, users)
    print(schedule_report(schedules))

    # Match escalation policies with their Grafana OnCall counterparts
    print("\n▶ Matching escalation policies...")
    for policy in escalation_policies:
        match_escalation_policy(policy, oncall_escalation_chains)
        match_users_and_schedules_for_escalation_policy(policy, users, schedules)
    print(escalation_policy_report(escalation_policies))

    # Match integrations with their Grafana OnCall counterparts
    print("\n▶ Matching integrations...")
    for integration in integrations:
        match_integration(integration, oncall_integrations)
        match_integration_type(integration)
        match_escalation_policy_for_integration(integration, escalation_policies)
    print(integration_report(integrations))

    if MODE == MODE_PLAN:
        return

    # Migrate users
    if MIGRATE_USERS:
        print("\n▶ Migrating users...")
        for user in users:
            if user.get("oncall_user"):
                print(f"{TAB}Migrating {format_user(user)}...")
                migrate_notification_rules(user)

    # Migrate schedules
    print("\n▶ Migrating schedules...")
    for schedule in schedules:
        if not schedule.get("migration_errors"):
            print(f"{TAB}Migrating {format_schedule(schedule)}...")
            migrate_schedule(schedule, user_id_map)

    # Migrate escalation policies
    print("\n▶ Migrating escalation policies...")
    for policy in escalation_policies:
        if policy.get("oncall_escalation_chain") is None:
            continue
        print(f"{TAB}Migrating {format_escalation_policy(policy)}...")
        migrate_escalation_policy(policy, users, schedules)

    # Migrate integrations
    print("\n▶ Migrating integrations...")
    for integration in integrations:
        if integration.get("oncall_integration") is None:
            continue
        print(f"{TAB}Migrating {format_integration(integration)}...")
        migrate_integration(integration, escalation_policies)
