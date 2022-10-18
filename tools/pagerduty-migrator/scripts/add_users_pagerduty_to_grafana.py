import os
import secrets
import sys
from urllib.parse import urljoin

import requests
from pdpyras import APISession

PAGERDUTY_API_TOKEN = os.environ["PAGERDUTY_API_TOKEN"]
PATH_USERS_GRAFANA = "/api/admin/users"
GRAFANA_URL = os.environ["GRAFANA_URL"]  # Example: http://localhost:3000
GRAFANA_USERNAME = os.environ["GRAFANA_USERNAME"]
GRAFANA_PASSWORD = os.environ["GRAFANA_PASSWORD"]
SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"


def list_pagerduty_users():
    session = APISession(PAGERDUTY_API_TOKEN)

    users = session.list_all("users")

    for user in users:
        password = secrets.token_urlsafe(15)
        username = user["email"].split("@")[0]
        json = {
            "name": user["name"],
            "email": user["email"],
            "login": username,
            "password": password,
        }
        create_grafana_user(json)


def create_grafana_user(data):
    url = urljoin(GRAFANA_URL, PATH_USERS_GRAFANA)
    response = requests.request(
        "POST", url, auth=(GRAFANA_USERNAME, GRAFANA_PASSWORD), json=data
    )

    if response.status_code == 200:
        print(SUCCESS_SIGN + " User created: " + data["login"])
    elif response.status_code == 401:
        sys.exit(ERROR_SIGN + " Invalid username or password.")
    elif response.status_code == 412:
        print(ERROR_SIGN + " User " + data["login"] + " already exists.")
    else:
        print("{} {}".format(ERROR_SIGN, response.text))


if __name__ == "__main__":
    list_pagerduty_users()
