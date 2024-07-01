import os
import sys

from pdpyras import APISession

from lib.grafana.api_client import GrafanaAPIClient
from lib.splunk.api_client import SplunkOnCallAPIClient

MIGRATING_FROM = os.environ["MIGRATING_FROM"]
PAGERDUTY = "pagerduty"
SPLUNK = "splunk"

PAGERDUTY_API_TOKEN = os.environ.get("PAGERDUTY_API_TOKEN")
SPLUNK_API_ID = os.environ.get("SPLUNK_API_ID")
SPLUNK_API_KEY = os.environ.get("SPLUNK_API_KEY")

GRAFANA_URL = os.environ["GRAFANA_URL"]  # Example: http://localhost:3000
GRAFANA_USERNAME = os.environ["GRAFANA_USERNAME"]
GRAFANA_PASSWORD = os.environ["GRAFANA_PASSWORD"]

SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"

grafana_client = GrafanaAPIClient(GRAFANA_URL, GRAFANA_USERNAME, GRAFANA_PASSWORD)


def migrate_pagerduty_users():
    session = APISession(PAGERDUTY_API_TOKEN)
    for user in session.list_all("users"):
        create_grafana_user(user["name"], user["email"])


def migrate_splunk_users():
    client = SplunkOnCallAPIClient(SPLUNK_API_ID, SPLUNK_API_KEY)
    for user in client.fetch_users(include_paging_policies=False):
        create_grafana_user(f"{user['firstName']} {user['lastName']}", user["email"])


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
    else:
        raise ValueError("Invalid value for MIGRATING_FROM")
