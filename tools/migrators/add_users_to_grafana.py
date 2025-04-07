import os
import sys

from pdpyras import APISession

from lib.grafana.api_client import GrafanaAPIClient
from lib.opsgenie.api_client import OpsGenieAPIClient
from lib.splunk.api_client import SplunkOnCallAPIClient

MIGRATING_FROM = os.environ["MIGRATING_FROM"]
PAGERDUTY = "pagerduty"
SPLUNK = "splunk"
OPSGENIE = "opsgenie"

PAGERDUTY_API_TOKEN = os.environ.get("PAGERDUTY_API_TOKEN")
SPLUNK_API_ID = os.environ.get("SPLUNK_API_ID")
SPLUNK_API_KEY = os.environ.get("SPLUNK_API_KEY")
OPSGENIE_API_KEY = os.environ.get("OPSGENIE_API_KEY")
OPSGENIE_API_URL = os.environ.get("OPSGENIE_API_URL", "https://api.opsgenie.com/v2")

GRAFANA_URL = os.environ["GRAFANA_URL"]  # Example: http://localhost:3000
GRAFANA_USERNAME = os.environ["GRAFANA_USERNAME"]
GRAFANA_PASSWORD = os.environ["GRAFANA_PASSWORD"]

# Get optional filter for PagerDuty user IDs
PAGERDUTY_FILTER_USERS = os.environ.get("PAGERDUTY_FILTER_USERS", "")
if PAGERDUTY_FILTER_USERS:
    PAGERDUTY_FILTER_USERS = PAGERDUTY_FILTER_USERS.split(",")
else:
    PAGERDUTY_FILTER_USERS = []

# Get optional filter for OpsGenie user IDs
OPSGENIE_FILTER_USERS = os.environ.get("OPSGENIE_FILTER_USERS", "")
if OPSGENIE_FILTER_USERS:
    OPSGENIE_FILTER_USERS = OPSGENIE_FILTER_USERS.split(",")
else:
    OPSGENIE_FILTER_USERS = []

SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"

grafana_client = GrafanaAPIClient(GRAFANA_URL, GRAFANA_USERNAME, GRAFANA_PASSWORD)


def migrate_pagerduty_users():
    """
    Migrate users from PagerDuty to Grafana.
    If PAGERDUTY_FILTER_USERS is set, only users with IDs in that list will be migrated.
    """
    session = APISession(PAGERDUTY_API_TOKEN)
    all_users = session.list_all("users")

    # Filter users if PAGERDUTY_FILTER_USERS is set
    if PAGERDUTY_FILTER_USERS:
        filtered_users = [
            user for user in all_users if user["id"] in PAGERDUTY_FILTER_USERS
        ]
        skipped_count = len(all_users) - len(filtered_users)
        if skipped_count > 0:
            print(f"Skipping {skipped_count} users not in PAGERDUTY_FILTER_USERS.")
        users_to_migrate = filtered_users
    else:
        users_to_migrate = all_users

    # Create Grafana users
    print(f"Creating {len(users_to_migrate)} users in Grafana...")
    for user in users_to_migrate:
        create_grafana_user(user["name"], user["email"])


def migrate_splunk_users():
    client = SplunkOnCallAPIClient(SPLUNK_API_ID, SPLUNK_API_KEY)
    for user in client.fetch_users(include_paging_policies=False):
        create_grafana_user(f"{user['firstName']} {user['lastName']}", user["email"])


def migrate_opsgenie_users():
    """
    Migrate users from OpsGenie to Grafana.
    If OPSGENIE_FILTER_USERS is set, only users with IDs in that list will be migrated.
    """
    client = OpsGenieAPIClient(OPSGENIE_API_KEY, OPSGENIE_API_URL)
    all_users = client.list_users()

    # Filter users if OPSGENIE_FILTER_USERS is set
    if OPSGENIE_FILTER_USERS:
        filtered_users = [
            user for user in all_users if user["id"] in OPSGENIE_FILTER_USERS
        ]
        skipped_count = len(all_users) - len(filtered_users)
        if skipped_count > 0:
            print(f"Skipping {skipped_count} users not in OPSGENIE_FILTER_USERS.")
        users_to_migrate = filtered_users
    else:
        users_to_migrate = all_users

    for user in users_to_migrate:
        create_grafana_user(user["fullName"], user["username"])


def create_grafana_user(name: str, email: str):
    response = grafana_client.create_user_with_random_password(name, email)

    if response.status_code == 200:
        print(SUCCESS_SIGN + " User created: " + email)
    elif response.status_code == 401:
        sys.exit(ERROR_SIGN + " Invalid username or password.")
    elif response.status_code == 412:
        print(ERROR_SIGN + " User " + email + " already exists.")
    else:
        print("{} {}".format(ERROR_SIGN, response.text))


if __name__ == "__main__":
    if MIGRATING_FROM == PAGERDUTY:
        migrate_pagerduty_users()
    elif MIGRATING_FROM == SPLUNK:
        migrate_splunk_users()
    elif MIGRATING_FROM == OPSGENIE:
        migrate_opsgenie_users()
    else:
        raise ValueError("Invalid value for MIGRATING_FROM")
