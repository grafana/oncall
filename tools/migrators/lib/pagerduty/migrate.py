import datetime

from pdpyras import APISession

from lib.common.report import TAB
from lib.common.resources.users import match_user
from lib.oncall.api_client import OnCallAPIClient
from lib.pagerduty.config import (
    EXPERIMENTAL_MIGRATE_EVENT_RULES,
    MIGRATE_USERS,
    MODE,
    MODE_PLAN,
    PAGERDUTY_API_TOKEN,
)
from lib.pagerduty.report import (
    escalation_policy_report,
    format_escalation_policy,
    format_integration,
    format_ruleset,
    format_schedule,
    format_user,
    integration_report,
    ruleset_report,
    schedule_report,
    user_report,
)
from lib.pagerduty.resources.escalation_policies import (
    match_escalation_policy,
    match_escalation_policy_for_integration,
    migrate_escalation_policy,
)
from lib.pagerduty.resources.integrations import (
    match_integration,
    match_integration_type,
    migrate_integration,
)
from lib.pagerduty.resources.notification_rules import migrate_notification_rules
from lib.pagerduty.resources.rulesets import match_ruleset, migrate_ruleset
from lib.pagerduty.resources.schedules import match_schedule, migrate_schedule
from lib.pagerduty.resources.users import (
    match_users_and_schedules_for_escalation_policy,
    match_users_for_schedule,
)


def migrate() -> None:
    session = APISession(PAGERDUTY_API_TOKEN)
    session.timeout = 20

    if MIGRATE_USERS:
        print("▶ Fetching users...")
        users = session.list_all("users", params={"include[]": "notification_rules"})
    else:
        print("▶ Skipping user migration as MIGRATE_USERS is false...")
        users = []

    oncall_users = OnCallAPIClient.list_users_with_notification_rules()

    print("▶ Fetching schedules...")
    # Fetch schedules from PagerDuty
    schedules = session.list_all(
        "schedules", params={"include[]": "schedule_layers", "time_zone": "UTC"}
    )

    # Fetch overrides from PagerDuty
    since = datetime.datetime.now(datetime.timezone.utc)
    until = since + datetime.timedelta(
        days=365
    )  # fetch overrides up to 1 year from now
    for schedule in schedules:
        response = session.jget(
            f"schedules/{schedule['id']}/overrides",
            params={"since": since.isoformat(), "until": until.isoformat()},
        )
        schedule["overrides"] = response["overrides"]

    # Fetch schedules from OnCall
    oncall_schedules = OnCallAPIClient.list_all("schedules")

    print("▶ Fetching escalation policies...")
    escalation_policies = session.list_all("escalation_policies")
    oncall_escalation_chains = OnCallAPIClient.list_all("escalation_chains")

    print("▶ Fetching integrations...")
    services = session.list_all("services", params={"include[]": "integrations"})
    vendors = session.list_all("vendors")

    integrations = []
    for service in services:
        service_integrations = service.pop("integrations")
        for integration in service_integrations:
            integration["service"] = service
            integrations.append(integration)

    oncall_integrations = OnCallAPIClient.list_all("integrations")

    rulesets = None
    if EXPERIMENTAL_MIGRATE_EVENT_RULES:
        print("▶ Fetching event rules (global rulesets)...")
        rulesets = session.list_all("rulesets")
        for ruleset in rulesets:
            rules = session.list_all(f"rulesets/{ruleset['id']}/rules")
            ruleset["rules"] = rules

    if MIGRATE_USERS:
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

    if rulesets is not None:
        for ruleset in rulesets:
            match_ruleset(
                ruleset,
                oncall_integrations,
                escalation_policies,
                services,
                integrations,
            )

    if MODE == MODE_PLAN:
        print(user_report(users), end="\n\n")
        print(schedule_report(schedules), end="\n\n")
        print(escalation_policy_report(escalation_policies), end="\n\n")
        print(integration_report(integrations), end="\n\n")

        if rulesets is not None:
            print(ruleset_report(rulesets), end="\n\n")

        return

    if MIGRATE_USERS:
        print("▶ Migrating user notification rules...")
        for user in users:
            if user["oncall_user"]:
                migrate_notification_rules(user)
                print(TAB + format_user(user))
    else:
        print(
            "▶ Skipping migrating user notification rules as MIGRATE_USERS is false..."
        )

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

    if rulesets is not None:
        print("▶ Migrating event rules (global rulesets)...")
        for ruleset in rulesets:
            if not ruleset["flawed_escalation_policies"]:
                migrate_ruleset(ruleset, escalation_policies, services)
                print(TAB + format_ruleset(ruleset))
