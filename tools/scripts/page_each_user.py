# requires requests (pip install requests)

# You can run it like this:
#    $ ONCALL_API_TOKEN=<api-token> python page_each_user.py

# This script will create an escalation chain, an escalation policy and a webhook integration
# to trigger alerts to each user in the organization. It will iterate over all users and update
# the escalation policy to notify each user, then trigger an alert group to page that user.

# By default the escalation chain will be named "Page each user", the integration will be named "Page each user".
# You can customize these names by setting the environment variables ESCALATION_NAME and INTEGRATION_NAME.
# NOTE: You need to remove the existing escalation chain and integration if you want to run this script again.


import os
import time

import requests

ONCALL_API_BASE_URL = os.environ.get(
    "ONCALL_API_BASE_URL",
    "https://oncall-prod-us-central-0.grafana.net/oncall",
)
ONCALL_API_TOKEN = os.environ.get("ONCALL_API_TOKEN")
ESCALATION_NAME = os.environ.get("ESCALATION_NAME", "Page each user")
INTEGRATION_NAME = os.environ.get("INTEGRATION_NAME", "Page each user")

headers = {
    "Authorization": ONCALL_API_TOKEN,
}


def setup_escalation():
    """Setup an escalation chain to be used by the paging integration."""
    response = requests.post(
        f"{ONCALL_API_BASE_URL}/api/v1/escalation_chains",
        headers=headers,
        json={"name": ESCALATION_NAME},
    )
    response.raise_for_status()
    return response.json()


def setup_escalation_policy(escalation_chain):
    """Setup a base escalation policy associated to the given escalation chain."""
    response = requests.post(
        f"{ONCALL_API_BASE_URL}/api/v1/escalation_policies",
        headers=headers,
        json={
            "escalation_chain_id": escalation_chain["id"],
            "type": "wait",
            "duration": 60,
        },
    )
    response.raise_for_status()
    return response.json()


def update_escalation_to_notify_user(escalation_policy, user):
    """Update the escalation policy to notify the given user."""
    response = requests.put(
        f"{ONCALL_API_BASE_URL}/api/v1/escalation_policies/{escalation_policy['id']}",
        headers=headers,
        json={
            "type": "notify_persons",
            "persons_to_notify": [user["id"]],
        },
    )
    response.raise_for_status()


def setup_integration(escalation_chain):
    """Setup a webhook integration to trigger alerts following the given escalation chain."""
    response = requests.post(
        f"{ONCALL_API_BASE_URL}/api/v1/integrations",
        headers=headers,
        json={
            "name": INTEGRATION_NAME,
            "type": "webhook",
            "default_route": {
                "escalation_chain_id": escalation_chain["id"],
            },
            "templates": {
                "web": {
                    "title": "{{ payload.title }}",
                }
            }
        },
    )
    response.raise_for_status()
    return response.json()


# setup escalation chain, escalation policy and integration

escalation_chain = setup_escalation()
escalation_policy = setup_escalation_policy(escalation_chain)
integration = setup_integration(escalation_chain)

# iterate users, update escalation policy and trigger alert group
page = 1
while True:
    url = ONCALL_API_BASE_URL + "/api/v1/users/"
    r = requests.get(url, params={"page": page}, headers=headers)
    r.raise_for_status()
    response_data = r.json()
    results = response_data.get("results")
    for u in results:
        print("Updating escalation for user", u["username"])
        update_escalation_to_notify_user(escalation_policy, u)

        print("Triggering alert group for user", u["username"])
        response = requests.post(
            integration["link"],
            headers=headers,
            json={
                "title": f"Paging user {u['username']}",
                "message": "Please acknowledge this alert"
            },
        )
        # wait a bit to avoid rate limiting (and allow alert processing before next one)
        time.sleep(5)

    page += 1
    total_pages = int(response_data.get("total_pages"))
    if page > total_pages:
        break
