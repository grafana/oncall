import os
import secrets
import sys
import requests

from urllib.parse import urljoin
from pdpyras import APISession

PAGERDUTY_API_TOKEN = os.environ["PAGERDUTY_API_TOKEN"]
PATH_USERS_GRAFANA = "/api/admin/users"
URL_GRAFANA = os.environ["URL_GRAFANA"] # Example: http://localhost:3000
USERNAME_GRAFANA = os.environ["USERNAME_GRAFANA"]
PASSWORD_GRAFANA = os.environ["PASSWORD_GRAFANA"]
SUCCESS_SIGN = "✅"
ERROR_SIGN = "❌"

def pd_list_users():

    session = APISession(PAGERDUTY_API_TOKEN)

    users = session.list_all("users")

    for user in users:
        password = secrets.token_urlsafe(15)
        username = user["email"].split("@")
        json = {"name": user["name"], "email": user["email"], "login": username, "password": password}
        post_grafana(json)

def post_grafana(data):
    url = urljoin(URL_GRAFANA, PATH_USERS_GRAFANA)
    response = requests.request("POST", url, auth=(USERNAME_GRAFANA, PASSWORD_GRAFANA), json=data)

    if response.status_code == 200:
        print(SUCCESS_SIGN + " User created: " + data["login"])
    elif response.status_code == 401:
        sys.exit(ERROR_SIGN + " Invalid username or password.")
    elif response.status_code == 412:
        print(ERROR_SIGN + " User " + data["login"] + " already exists." )
    else: 
        print("{} {}".format(ERROR_SIGN, response.text))

if __name__ == "__main__":
    pd_list_users()
