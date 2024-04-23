from lib.common.report import TAB, WARNING_SIGN
from lib.common.resources.users import match_user
from lib.oncall.api_client import OnCallAPIClient
from lib.splunk.api_client import SplunkOnCallAPIClient
from lib.splunk.config import MODE, MODE_PLAN, SPLUNK_API_ID, SPLUNK_API_KEY
from lib.splunk.report import (
    escalation_policy_report,
    format_escalation_policy,
    format_schedule,
    format_user,
    schedule_report,
    user_report,
)
from lib.splunk.resources.escalation_policies import (
    match_escalation_policy,
    match_users_and_schedules_for_escalation_policy,
    migrate_escalation_policy,
)
from lib.splunk.resources.paging_policies import migrate_paging_policies
from lib.splunk.resources.schedules import match_schedule, migrate_schedule


def migrate():
    # NOTE: uncomment out the following code if we consider auto-migration of teams
    # grafana_api_client = GrafanaAPIClient(
    #     GRAFANA_URL, GRAFANA_USERNAME, GRAFANA_PASSWORD
    # )
    splunk_client = SplunkOnCallAPIClient(SPLUNK_API_ID, SPLUNK_API_KEY)

    print("▶ Fetching users...")
    oncall_users = OnCallAPIClient.list_users_with_notification_rules()
    splunk_users = splunk_client.fetch_users()

    # NOTE: uncomment out the following code if we consider auto-migration of teams
    # print("▶ Fetching teams...")
    # splunk_teams = splunk_client.fetch_teams(include_members=True)
    # oncall_teams = OnCallAPIClient.list_all("teams")

    print("▶ Fetching schedules...")
    oncall_schedules = OnCallAPIClient.list_all("schedules")
    splunk_schedules = splunk_client.fetch_schedules()

    print("▶ Fetching escalation policies...")
    splunk_escalation_policies = splunk_client.fetch_escalation_policies()
    oncall_escalation_chains = OnCallAPIClient.list_all("escalation_chains")

    for splunk_user in splunk_users:
        match_user(splunk_user, oncall_users)

    splunk_username_to_oncall_user_id_map = {
        u["username"]: u["oncall_user"]["id"] if u["oncall_user"] else None
        for u in splunk_users
    }

    # NOTE: uncomment out the following code if we consider auto-migration of teams
    # splunk_username_to_email_map = {
    #     user["username"]: user["email"] for user in splunk_users
    # }

    # for splunk_team in splunk_teams:
    #     match_team(splunk_team, oncall_teams)

    # oncall_team_name_to_id_map = {team["name"]: team["id"] for team in oncall_teams}
    # splunk_team_slug_to_grafana_team_id_map: typing.Dict[str, int] = {}

    # NOTE: this team mapping won't quite work.. this creates and returns a mapping of
    # Splunk team slugs to Grafana team IDs.. however, we actually need to map Splunk team
    # slugs to OnCall team public primary keys (IDs)
    #
    # NOTE: we need to map this beforehand so that we can build the Splunk team slug to Grafana team id mapping
    # print("▶ Migrating teams and team members...")
    # for splunk_team in splunk_teams:
    #     member_emails = [
    #         splunk_username_to_email_map[member["username"]]
    #         for member in splunk_team["members"]
    #         if member["username"] in splunk_username_to_email_map
    #     ]
    #     grafana_team_id = grafana_api_client.idemopotently_create_team_and_add_users(splunk_team["name"], member_emails)
    #     print(TAB + format_team(splunk_team))

    #     splunk_team_slug_to_grafana_team_id_map[splunk_team["slug"]] = grafana_team_id

    for splunk_schedule in splunk_schedules:
        match_schedule(
            splunk_schedule, oncall_schedules, splunk_username_to_oncall_user_id_map
        )

    for splunk_escalation_policy in splunk_escalation_policies:
        match_escalation_policy(splunk_escalation_policy, oncall_escalation_chains)
        match_users_and_schedules_for_escalation_policy(
            splunk_escalation_policy, splunk_users, splunk_schedules
        )

    if MODE == MODE_PLAN:
        print(user_report(splunk_users), end="\n\n")
        print(schedule_report(splunk_schedules), end="\n\n")
        print(escalation_policy_report(splunk_escalation_policies), end="\n\n")

        return

    print("▶ Migrating user paging policies...")
    for splunk_user in splunk_users:
        if splunk_user["oncall_user"]:
            migrate_paging_policies(splunk_user)
            print(TAB + format_user(splunk_user))

    print("▶ Migrating schedules...")
    for splunk_schedule in splunk_schedules:
        if not splunk_schedule["migration_errors"]:
            migrate_schedule(splunk_schedule, splunk_username_to_oncall_user_id_map)
            print(TAB + format_schedule(splunk_schedule))
        else:
            print(
                TAB
                + WARNING_SIGN
                + f" skipping {splunk_schedule['name']} due to migration errors, see `plan` output for more details"
            )

    print("▶ Migrating escalation policies...")
    for splunk_escalation_policy in splunk_escalation_policies:
        if (
            not splunk_escalation_policy["unmatched_users"]
            and not splunk_escalation_policy["flawed_schedules"]
        ):
            migrate_escalation_policy(
                splunk_escalation_policy, splunk_users, splunk_schedules
            )
            print(TAB + format_escalation_policy(splunk_escalation_policy))
