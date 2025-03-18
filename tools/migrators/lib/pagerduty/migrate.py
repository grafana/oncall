import datetime
import re
from typing import Any, Dict, List

from pdpyras import APISession

from lib.common.report import TAB
from lib.common.resources.services import filter_services
from lib.common.resources.users import match_user
from lib.grafana.service_migrate import migrate_all_services
from lib.grafana.service_model_client import ServiceModelClient
from lib.oncall.api_client import OnCallAPIClient
from lib.pagerduty.config import (
    EXPERIMENTAL_MIGRATE_EVENT_RULES,
    MIGRATE_USERS,
    MODE,
    MODE_PLAN,
    PAGERDUTY_API_TOKEN,
    PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX,
    PAGERDUTY_FILTER_INTEGRATION_REGEX,
    PAGERDUTY_FILTER_SCHEDULE_REGEX,
    PAGERDUTY_FILTER_TEAM,
    PAGERDUTY_FILTER_USERS,
    PAGERDUTY_MIGRATE_SERVICES,
    VERBOSE_LOGGING,
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
    services_report,
    user_report,
)
from lib.pagerduty.resources.business_service import (
    BusinessService,
    get_all_business_services_with_metadata,
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
from lib.pagerduty.resources.services import (
    TechnicalService,
    get_all_technical_services_with_metadata,
)
from lib.pagerduty.resources.users import (
    match_users_and_schedules_for_escalation_policy,
    match_users_for_schedule,
)


def filter_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def filter_schedules(schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter schedules based on configured filters.

    If multiple filters are specified, a schedule only needs to match one of them
    to be included (OR operation between filters).
    """
    if not any(
        [PAGERDUTY_FILTER_TEAM, PAGERDUTY_FILTER_USERS, PAGERDUTY_FILTER_SCHEDULE_REGEX]
    ):
        return schedules  # No filters specified, return all

    filtered_schedules = []
    filtered_out = 0
    filtered_reasons = {}

    for schedule in schedules:
        matches_any_filter = False
        reasons = []

        # Filter by team
        if PAGERDUTY_FILTER_TEAM:
            teams = schedule.get("teams", [])
            if any(team["summary"] == PAGERDUTY_FILTER_TEAM for team in teams):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No teams found for team filter: {PAGERDUTY_FILTER_TEAM}"
                )

        # Filter by users
        if PAGERDUTY_FILTER_USERS:
            schedule_users = set()
            for layer in schedule.get("schedule_layers", []):
                for user in layer.get("users", []):
                    schedule_users.add(user["user"]["id"])

            if any(user_id in schedule_users for user_id in PAGERDUTY_FILTER_USERS):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No users found for user filter: {','.join(PAGERDUTY_FILTER_USERS)}"
                )

        # Filter by name regex
        if PAGERDUTY_FILTER_SCHEDULE_REGEX:
            if re.match(PAGERDUTY_FILTER_SCHEDULE_REGEX, schedule["name"]):
                matches_any_filter = True
            else:
                reasons.append(
                    f"Schedule regex filter: {PAGERDUTY_FILTER_SCHEDULE_REGEX}"
                )

        if matches_any_filter:
            filtered_schedules.append(schedule)
        else:
            filtered_out += 1
            filtered_reasons[schedule["id"]] = reasons

    if filtered_out > 0:
        summary = f"Filtered out {filtered_out} schedules"
        print(summary)

        # Only print detailed reasons in verbose mode
        if VERBOSE_LOGGING:
            for schedule_id, reasons in filtered_reasons.items():
                print(f"{TAB}Schedule {schedule_id}: {', '.join(reasons)}")

    return filtered_schedules


def filter_escalation_policies(policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter escalation policies based on configured filters.

    If multiple filters are specified, a policy only needs to match one of them
    to be included (OR operation between filters).
    """
    if not any(
        [
            PAGERDUTY_FILTER_TEAM,
            PAGERDUTY_FILTER_USERS,
            PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX,
        ]
    ):
        return policies  # No filters specified, return all

    filtered_policies = []
    filtered_out = 0
    filtered_reasons = {}

    for policy in policies:
        matches_any_filter = False
        reasons = []

        # Filter by team
        if PAGERDUTY_FILTER_TEAM:
            teams = policy.get("teams", [])
            if any(team["summary"] == PAGERDUTY_FILTER_TEAM for team in teams):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No teams found for team filter: {PAGERDUTY_FILTER_TEAM}"
                )

        # Filter by users
        if PAGERDUTY_FILTER_USERS:
            policy_users = set()
            for rule in policy.get("escalation_rules", []):
                for target in rule.get("targets", []):
                    if target["type"] == "user":
                        policy_users.add(target["id"])

            if any(user_id in policy_users for user_id in PAGERDUTY_FILTER_USERS):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No users found for user filter: {','.join(PAGERDUTY_FILTER_USERS)}"
                )

        # Filter by name regex
        if PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX:
            if re.match(PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX, policy["name"]):
                matches_any_filter = True
            else:
                reasons.append(
                    f"Escalation policy regex filter: {PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX}"
                )

        if matches_any_filter:
            filtered_policies.append(policy)
        else:
            filtered_out += 1
            filtered_reasons[policy["id"]] = reasons

    if filtered_out > 0:
        summary = f"Filtered out {filtered_out} escalation policies"
        print(summary)

        # Only print detailed reasons in verbose mode
        if VERBOSE_LOGGING:
            for policy_id, reasons in filtered_reasons.items():
                print(f"{TAB}Policy {policy_id}: {', '.join(reasons)}")

    return filtered_policies


def filter_integrations(integrations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter integrations based on configured filters.

    If multiple filters are specified, an integration only needs to match one of them
    to be included (OR operation between filters).
    """
    if not any([PAGERDUTY_FILTER_TEAM, PAGERDUTY_FILTER_INTEGRATION_REGEX]):
        return integrations  # No filters specified, return all

    filtered_integrations = []
    filtered_out = 0
    filtered_reasons = {}

    for integration in integrations:
        matches_any_filter = False
        reasons = []

        # Filter by team
        if PAGERDUTY_FILTER_TEAM:
            teams = integration["service"].get("teams", [])
            if any(team["summary"] == PAGERDUTY_FILTER_TEAM for team in teams):
                matches_any_filter = True
            else:
                reasons.append(
                    f"No teams found for team filter: {PAGERDUTY_FILTER_TEAM}"
                )

        # Filter by name regex
        if PAGERDUTY_FILTER_INTEGRATION_REGEX:
            integration_name = (
                f"{integration['service']['name']} - {integration['name']}"
            )
            if re.match(PAGERDUTY_FILTER_INTEGRATION_REGEX, integration_name):
                matches_any_filter = True
            else:
                reasons.append(
                    f"Integration regex filter: {PAGERDUTY_FILTER_INTEGRATION_REGEX}"
                )

        if matches_any_filter:
            filtered_integrations.append(integration)
        else:
            filtered_out += 1
            filtered_reasons[integration["id"]] = reasons

    if filtered_out > 0:
        summary = f"Filtered out {filtered_out} integrations"
        print(summary)

        # Only print detailed reasons in verbose mode
        if VERBOSE_LOGGING:
            for integration_id, reasons in filtered_reasons.items():
                print(f"{TAB}Integration {integration_id}: {', '.join(reasons)}")

    return filtered_integrations


def migrate() -> None:
    # Set up API sessions and timeout
    session = APISession(PAGERDUTY_API_TOKEN)
    session.timeout = 20

    # Use a flag to track how many resources were eligible for migration in the final report
    filtered_resources_summary = {
        "schedules": 0,
        "escalation_policies": 0,
        "integrations": 0,
    }

    # Process users only if MIGRATE_USERS is true
    users = []
    oncall_users = []
    user_id_map = {}

    if MIGRATE_USERS:
        print("▶ Fetching users...")
        users = session.list_all("users", params={"include[]": "notification_rules"})
        oncall_users = OnCallAPIClient.list_users_with_notification_rules()

        # Apply filtering to users if specified
        if PAGERDUTY_FILTER_USERS:
            print("▶ Filtering users based on PAGERDUTY_FILTER_USERS...")
            users = filter_users(users)

        # Match users with Grafana OnCall users
        for user in users:
            match_user(user, oncall_users)

        # Create a mapping from PagerDuty user IDs to Grafana OnCall user IDs
        user_id_map = {
            u["id"]: u["oncall_user"]["id"] if u["oncall_user"] else None for u in users
        }
    else:
        print("▶ Skipping user fetching and migration as MIGRATE_USERS is false...")

    print("▶ Fetching schedules...")
    # Fetch schedules from PagerDuty
    schedules = session.list_all(
        "schedules",
        params={"include[]": ["schedule_layers", "teams"], "time_zone": "UTC"},
    )

    # Apply filters to schedules
    schedules = filter_schedules(schedules)
    filtered_resources_summary["schedules"] = len(schedules)
    print(f"Found {len(schedules)} schedules after filtering")

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
    escalation_policies = session.list_all(
        "escalation_policies", params={"include[]": "teams"}
    )

    # Apply filters to escalation policies
    escalation_policies = filter_escalation_policies(escalation_policies)
    filtered_resources_summary["escalation_policies"] = len(escalation_policies)
    print(f"Found {len(escalation_policies)} escalation policies after filtering")

    oncall_escalation_chains = OnCallAPIClient.list_all("escalation_chains")

    print("▶ Fetching integrations...")
    services = session.list_all(
        "services", params={"include[]": ["integrations", "teams"]}
    )
    vendors = session.list_all("vendors")

    integrations = []
    for service in services:
        service_integrations = service.pop("integrations")
        for integration in service_integrations:
            integration["service"] = service
            integrations.append(integration)

    # Apply filters to integrations
    integrations = filter_integrations(integrations)
    filtered_resources_summary["integrations"] = len(integrations)
    print(f"Found {len(integrations)} integrations after filtering")

    oncall_integrations = OnCallAPIClient.list_all("integrations")

    rulesets = None
    if EXPERIMENTAL_MIGRATE_EVENT_RULES:
        print("▶ Fetching event rules (global rulesets)...")
        rulesets = session.list_all("rulesets")
        for ruleset in rulesets:
            rules = session.list_all(f"rulesets/{ruleset['id']}/rules")
            ruleset["rules"] = rules

    # Match resources if we have users
    for schedule in schedules:
        match_schedule(schedule, oncall_schedules, user_id_map)
        if MIGRATE_USERS:
            match_users_for_schedule(schedule, users)
        else:
            # When not migrating users, mark schedule as having no unmatched users
            schedule["unmatched_users"] = []
            schedule["migration_errors"] = []

    for policy in escalation_policies:
        match_escalation_policy(policy, oncall_escalation_chains)
        if MIGRATE_USERS:
            match_users_and_schedules_for_escalation_policy(policy, users, schedules)
        else:
            # When not migrating users, mark policy as having no unmatched users
            policy["unmatched_users"] = []
            policy["flawed_schedules"] = []

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

    if PAGERDUTY_MIGRATE_SERVICES:
        client = ServiceModelClient()
        # Get all services
        all_technical_services = get_all_technical_services_with_metadata(session)
        technical_service_map = {
            service.id: service for service in all_technical_services
        }
        all_business_services = get_all_business_services_with_metadata(
            session, technical_service_map
        )

        # Apply filters to services
        filtered_technical_data = filter_services(
            [service.raw_data for service in all_technical_services], TAB
        )
        filtered_business_data = filter_services(
            [service.raw_data for service in all_business_services], TAB
        )

        # Convert filtered data back to service objects
        technical_services = [
            TechnicalService(service) for service in filtered_technical_data
        ]
        business_services = [
            BusinessService(service) for service in filtered_business_data
        ]

    # Print filtering and matching summary
    print("\n▶ Migration summary after filtering and matching:")
    if MIGRATE_USERS:
        print(
            f"Users: {sum(1 for u in users if u.get('oncall_user'))} matched of {len(users)} total"
        )
    print(
        f"Schedules: {sum(1 for s in schedules if not s.get('unmatched_users') and not s.get('migration_errors'))} eligible of {filtered_resources_summary['schedules']} filtered"
    )
    print(
        f"Escalation policies: {sum(1 for p in escalation_policies if not p.get('unmatched_users') and not p.get('flawed_schedules'))} eligible of {filtered_resources_summary['escalation_policies']} filtered"
    )
    print(
        f"Integrations: {sum(1 for i in integrations if i.get('oncall_type') and not i.get('is_escalation_policy_flawed'))} eligible of {filtered_resources_summary['integrations']} filtered"
    )
    print("")

    if MODE == MODE_PLAN:
        if MIGRATE_USERS:
            print(user_report(users), end="\n\n")
        print(schedule_report(schedules), end="\n\n")
        print(escalation_policy_report(escalation_policies), end="\n\n")
        print(integration_report(integrations), end="\n\n")

        if rulesets is not None:
            print(ruleset_report(rulesets), end="\n\n")

        if PAGERDUTY_MIGRATE_SERVICES:
            print(
                services_report(
                    all_technical_services,
                    all_business_services,
                    technical_services,
                    business_services,
                ),
                end="\n\n",
            )

            return

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

    if PAGERDUTY_MIGRATE_SERVICES:
        print("▶ Migrating services to Grafana's service model...")
        migrate_all_services(
            client, technical_services, business_services, dry_run=False
        )
    else:
        print("▶ Skipping service migration as PAGERDUTY_MIGRATE_SERVICES is false...")
