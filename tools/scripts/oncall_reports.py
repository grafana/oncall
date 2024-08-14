# requires requests (pip install requests)

# This script will output 4 .csv files:
#   - oncall.escalation_chains.csv: escalation chains names and their respective serialized steps
#   - oncall.orphaned_schedules.csv: schedules ID and name for schedules not linked to any escalation chain
#   - oncall.teams.csv: teams alert groups count, mean time to acknowledge and mean time to resolve
#   - oncall.users.csv: users information in the speficied period
#       (team, notification policies, hours on-call, has shifts scheduled, # acknowledged, # resolved)

# You can run it like this:
#    $ ONCALL_API_TOKEN=<api-token> DAYS=7 python oncall_reports.py

import collections
import csv
import os

from datetime import datetime, timedelta, timezone

import requests

ONCALL_API_BASE_URL = os.environ.get(
    "ONCALL_API_BASE_URL",
    "https://oncall-prod-us-central-0.grafana.net/oncall",
)
ONCALL_API_TOKEN = os.environ.get("ONCALL_API_TOKEN")

# number of days to consider (default: last 30 days)
NUM_LAST_DAYS = int(os.environ.get("DAYS", 30))
REQUIRED_PERSONAL_NOTIFICATION_METHODS = ["phone_call", "mobile_app"]

# output CSV filenames with the data
ESCALATION_CHAINS_OUTPUT_FILE_NAME = "oncall.escalation_chains.csv"
ORPHANED_SCHEDULES_OUTPUT_FILE_NAME = "oncall.orphaned_schedules.csv"
TEAMS_OUTPUT_FILE_NAME = "oncall.teams.csv"
USERS_OUTPUT_FILE_NAME = "oncall.users.csv"


headers = {
    "Authorization": ONCALL_API_TOKEN,
}

users = {}
teams = {}
escalation_chains = {}
integrations = {}
schedules = {}
ag_per_team = collections.defaultdict(int)
ttr_acc = collections.defaultdict(int)
tta_acc = collections.defaultdict(int)

end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, microsecond=0)
start_date = end_date - timedelta(days=NUM_LAST_DAYS)
hours_field_name = "hours_on_call_last_{}d".format(NUM_LAST_DAYS)

def _serialize_step(p):
    step = p["type"]
    if step == "wait":
        step = "{}({})".format(p["type"], p["duration"])
    elif step == "trigger_webhook":
        step = "{}({})".format(p["type"], p["action_to_trigger"])
    elif step ==  "notify_user_group":
        step = "{}({})".format(p["type"], p["group_to_notify"])
    elif step == "notify_persons":
        step = "{}({})".format(
            p["type"],
            ','.join(users[u_id]["username"] for u_id in p["persons_to_notify"]) if p["persons_to_notify"] else '',
        )
    elif step == "notify_on_call_from_schedule":
        schedule_id = p["notify_on_call_from_schedule"]
        step = "{}({})".format(
            p["type"],
            schedules.get(schedule_id, "missing") if schedule_id else '',
        )
    elif step == "notify_if_time_from_to":
        step = "{}({}-{})".format(p["type"], p["notify_if_time_from"], p["notify_if_time_to"])
    return step

# fetch teams
# GET {{API_URL}}/api/v1/teams/

print("Fetching teams data...")
url = ONCALL_API_BASE_URL + "/api/v1/teams/"
r = requests.get(url, params={"perpage": 100}, headers=headers)  # TODO: handle pagination
r.raise_for_status()
results = r.json().get("results")
for t in results:
    teams[t["id"]] = t["name"]


# fetch users
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/users/#list-users
# GET {{API_URL}}/api/v1/users/

print("Fetching users data...")
page = 1
while True:
    url = ONCALL_API_BASE_URL + "/api/v1/users/"
    r = requests.get(url, params={"page": page}, headers=headers)
    r.raise_for_status()
    response_data = r.json()
    results = response_data.get("results")
    for u in results:
        users[u["id"]] = {
            "username": u["username"],
            "email": u["email"],
            "teams": ",".join([teams[t] for t in u["teams"]]),
            "acknowledged_count": 0,
            "resolved_count": 0,
            hours_field_name: 0,
            "shifts_scheduled": False,
        }
    page += 1
    total_pages = int(response_data.get("total_pages"))
    if page > total_pages:
        break

# fetch policies
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/personal_notification_rules/#list-personal-notification-rules
# {{API_URL}}/api/v1/personal_notification_rules/ ?user_id= & important=

print("Fetching users notification policies...")
url = ONCALL_API_BASE_URL + "/api/v1/personal_notification_rules/"
for u in users:
    for important in ("true", "false"):
        r = requests.get(url, params={"user_id": u, "important": important}, headers=headers)
        r.raise_for_status()
        results = r.json().get("results")
        policy = ",".join(_serialize_step(p) for p in results)
        key = "important" if important == "true" else "default"
        users[u][key] = policy


# fetch integrations
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/integrations/#list-integrations
# GET {{API_URL}}/api/v1/integrations/
print("Fetching integrations data...")
url = ONCALL_API_BASE_URL + "/api/v1/integrations/"
r = requests.get(url, params={"perpage": 100}, headers=headers)  # TODO: handle pagination
r.raise_for_status()
results = r.json().get("results")
for i in results:
    integrations[i["id"]] = i


# get on-call schedule time
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/schedules/#export-a-schedules-final-shifts

print("Fetching schedules/shifts data...")
url = ONCALL_API_BASE_URL + "/api/v1/schedules"
r = requests.get(url, headers=headers)
r.raise_for_status()
results = r.json().get("results")
for schedule in results:
    schedules[schedule["id"]] = schedule["name"]
    schedule_id = schedule["id"]
    url = ONCALL_API_BASE_URL + "/api/v1/schedules/{}/final_shifts".format(schedule_id)
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    shifts = r.json().get("results")
    for final_shift in shifts:
        user_pk = final_shift["user_pk"]
        end = datetime.fromisoformat(final_shift["shift_end"].replace('Z', '+00:00'))
        start = datetime.fromisoformat(final_shift["shift_start"].replace('Z', '+00:00'))
        shift_time_in_seconds = (end - start).total_seconds()
        shift_time_in_hours = shift_time_in_seconds / (60 * 60)
        on_call_hours = users.get(user_pk, {}).get(hours_field_name, 0)
        users[user_pk][hours_field_name] = on_call_hours + shift_time_in_hours


# fetch alert groups
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/alertgroups/#list-alert-groups
# GET {{API_URL}}/api/v1/alert_groups/

print("Fetching alert groups data...")
page = 1
in_range = True
while in_range:
    url = ONCALL_API_BASE_URL + "/api/v1/alert_groups"
    r = requests.get(url, params={"page": page}, headers=headers)
    r.raise_for_status()
    results = r.json().get("results")
    for ag in results:
        created_at = datetime.fromisoformat(ag["created_at"].replace('Z', '+00:00'))
        if created_at < start_date:
            in_range = False
            break
        ack_by = ag["acknowledged_by"]
        resolved_by = ag["resolved_by"]
        if ack_by:
            users[ack_by]["acknowledged_count"] += 1
        if resolved_by:
            users[resolved_by]["resolved_count"] += 1
        team_id = integrations.get(ag["integration_id"], {}).get("team_id", None)
        ag_per_team[team_id] += 1
        if ag["acknowledged_at"]:
            acknowledged_at = datetime.fromisoformat(ag["acknowledged_at"].replace('Z', '+00:00'))
            tta_acc[team_id] += (acknowledged_at - created_at).total_seconds()
        if ag["resolved_at"]:
            resolved_at = datetime.fromisoformat(ag["resolved_at"].replace('Z', '+00:00'))
            ttr_acc[team_id] += (resolved_at - created_at).total_seconds()
    page += 1


# fetch escalation chains
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/escalation_chains/#list-escalation-chains
# GET {{API_URL}}/api/v1/escalation_chains/

print("Fetching escalation chains data...")
url = ONCALL_API_BASE_URL + "/api/v1/escalation_chains/"
r = requests.get(url, params={"perpage": 100}, headers=headers)
r.raise_for_status()
results = r.json().get("results")
orphaned_schedules = set(schedules.keys())
for chain in results:
    chain_id = chain["id"]
    # fetch policies for escalation chain
    # https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/escalation_policies/#list-escalation-policies
    # GET {{API_URL}}/api/v1/escalation_policies/
    url = ONCALL_API_BASE_URL + "/api/v1/escalation_policies/"
    r = requests.get(url, params={"escalation_chain_id": chain_id}, headers=headers)
    r.raise_for_status()
    results = r.json().get("results")
    steps = ",".join(_serialize_step(p) for p in results)
    escalation_chains[chain_id] = {"name": chain["name"], "steps": steps}
    notify_schedules = [s for s in results if s["type"] == "notify_on_call _from_schedule"]
    for s in notify_schedules:
        # remove schedule from potential orphaned schedules
        schedule_id = s["notify_on_call _from_schedule"]
        orphaned_schedules.remove(schedule_id)


# check shifts from non-orphaned schedules, flag users shifts
# https://grafana.com/docs/grafana-cloud/alerting-and-irm/oncall/oncall-api-reference/on_call_shifts/#list-oncall-shifts
# GET {{API_URL}}/api/v1/on_call_shifts/?schedule_id=

print("Checking shifts from non-orphaned schedules...")
for schedule_id in schedules:
    if schedule_id in orphaned_schedules:
        continue
    url = ONCALL_API_BASE_URL + "/api/v1/on_call_shifts/"
    r = requests.get(url, params={"schedule_id": schedule_id}, headers=headers)
    r.raise_for_status()
    results = r.json().get("results")
    for shift in results:
        on_call_users = shift.get("users", []) + list({u for r in shift.get("rolling_users", []) for u in r})
        for user_id in on_call_users:
            if user_id not in users:
                print("Warning: user {} from schedule {} not found".format(user_id, schedule_id))
            else:
                users[user_id]["shifts_scheduled"] = True


# write orphaned schedules report
with open(ORPHANED_SCHEDULES_OUTPUT_FILE_NAME, "w") as fp:
    fieldnames = ["schedule_id", "name"]
    csv_writer = csv.DictWriter(fp, fieldnames)
    csv_writer.writeheader()
    for s_id in orphaned_schedules:
        row = {"schedule_id": s_id, "name": schedules[s_id]}
        csv_writer.writerow(row)


# write escalation chains report
with open(ESCALATION_CHAINS_OUTPUT_FILE_NAME, "w") as fp:
    fieldnames = ["name", "steps"]
    csv_writer = csv.DictWriter(fp, fieldnames)
    csv_writer.writeheader()
    for chain_info in escalation_chains.values():
        csv_writer.writerow(chain_info)


# write teams report
with open(TEAMS_OUTPUT_FILE_NAME, "w") as fp:
    fieldnames = ["team", "alert_group_count", "mtta", "mttr"]
    csv_writer = csv.DictWriter(fp, fieldnames)
    csv_writer.writeheader()
    for team_id, ag_count in ag_per_team.items():
        team_name = teams[team_id] if team_id else "(None)"
        csv_writer.writerow({
            "team": team_name,
            "alert_group_count": ag_count,
            "mtta": tta_acc[team_id] / ag_count,
            "mttr": ttr_acc[team_id] / ag_count,
        })


# write users report
with open(USERS_OUTPUT_FILE_NAME, "w") as fp:
    fieldnames = ["username", "email", "teams", "important", "default", "warning", hours_field_name, "shifts_scheduled", "acknowledged_count", "resolved_count"]
    csv_writer = csv.DictWriter(fp, fieldnames)
    csv_writer.writeheader()
    for user_info in users.values():
        warnings = []
        for method in REQUIRED_PERSONAL_NOTIFICATION_METHODS:
            expected = "notify_by_{}".format(method)
            if expected not in user_info["important"] and method not in user_info["default"]:
                warnings.append("Missing {}".format(method))
        user_info["warning"] = ','.join(warnings)
        csv_writer.writerow(user_info)
