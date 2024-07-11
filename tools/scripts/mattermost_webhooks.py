import json
import requests

# this script will get the mattermost channel ID using the mattermost API and
# setup OnCall webhooks to send and update notifications for alert group created/updated triggers

# Configuration
ONCALL_API_BASE_URL = "https://oncall-prod-us-central-0.grafana.net/oncall"
ONCALL_TOKEN = "<oncall API token>"
ONCALL_WEBHOOK_PREFIX = "mattermost"  # prefix for webhooks naming
MATTERMOST_API_BASE_URL = "http://localhost:8065"
MATTERMOST_BOT_TOKEN = "<mattermost bot user token>"
MATTERMOST_TEAM_NAME = "testing"  # mattermost team name to which the bot belongs to
MATTERMOST_CHANNEL_NAME = "testing"  # mattermost channel the bot user will post notifications (should be a member too)

NOTIFICATION_TEMPLATE = """
{% if alert_group.state == 'acknowledged'%}:large_orange_circle:{% elif alert_group.state == 'resolved'%}:large_green_circle:{% elif alert_group.state == 'silenced'%}:white_circle:{% else %}:red_circle:{% endif %} **{{ alert_group.title }}**
*{{ alert_group.state }}*
{{ alert_payload.message }}
*{{ integration.name }}*

{% if event.type == 'acknowledge' %}**Acknowledged by: {{ user.username }}**{% endif %}{% if event.type == 'resolve' %}**Resolved by: {{ user.username }}**{% endif %}{% if event.type == 'silence' %}**Silenced by: {{ user.username }} (until {{ event.until }})**{% endif %}

[View in Grafana OnCall]({{ alert_group.permalinks.web }})
"""

# --- Do not edit below this line ---

MATTERMOST_API_HEADERS = {
    "Authorization": "Bearer {}".format(MATTERMOST_BOT_TOKEN),
}

def get_mattermost_channel_id():
    url = "{}/api/v4/teams/name/{}/channels/name/{}".format(
        MATTERMOST_API_BASE_URL, MATTERMOST_TEAM_NAME, MATTERMOST_CHANNEL_NAME
    )
    r = requests.get(url, headers=MATTERMOST_API_HEADERS)
    r.raise_for_status()
    return r.json()["id"]


def get_oncall_webhook(name):
    webhook_uid = None
    oncall_url = "{}/api/v1/webhooks/?name={}".format(ONCALL_API_BASE_URL, name)
    oncall_api_headers = {
        "Authorization": ONCALL_TOKEN
    }
    r = requests.get(oncall_url, headers=oncall_api_headers)
    r.raise_for_status()
    results = r.json().get("results", [])
    if results:
        webhook_uid = results[0]["id"]
    return webhook_uid


def setup_oncall_webhook(name, trigger, http_method, endpoint, additional_data=None):
    url = "{}{}".format(MATTERMOST_API_BASE_URL, endpoint)
    headers = MATTERMOST_API_HEADERS
    data = {"message": NOTIFICATION_TEMPLATE}
    if additional_data is not None:
        data.update(additional_data)
    webhook_name = "{}-{}".format(ONCALL_WEBHOOK_PREFIX, name)
    # check if already exists
    webhook_uid = get_oncall_webhook(webhook_name)
    # create webhook here/ oncall api here
    oncall_url = "{}/api/v1/webhooks/".format(ONCALL_API_BASE_URL)
    oncall_api_headers = {
        "Authorization": ONCALL_TOKEN
    }
    oncall_http_method = "POST"
    webhook_data = {
        "name": webhook_name,
        "url": url,
        "http_method": http_method,
        "trigger_type": trigger,
        "forward_all": False,
        "data": json.dumps(data),
        "authorization_header": MATTERMOST_API_HEADERS["Authorization"],
    }
    if webhook_uid:
        webhook_data["id"] = webhook_uid
        oncall_url += webhook_uid
        oncall_http_method = "PUT"
    r = requests.request(
        oncall_http_method, oncall_url, headers=oncall_api_headers, json=webhook_data
    )
    r.raise_for_status()
    return r


# get mattermost channel id from name
channel_id = get_mattermost_channel_id()

# setup webhook for new alert group
endpoint = "/api/v4/posts"
new_ag_webhook = setup_oncall_webhook(
    "new", "alert group created", "POST", endpoint,
    additional_data={
        "channel_id": channel_id,
        "metadata": {
            "alert_group_id": "{{ alert_group.id }}"
        }
    }
)

# setup webhook for status changes
webhook_create_id = new_ag_webhook.json()["id"]
update_endpoint = "/api/v4/posts/{{{{ responses.{}.id }}}}".format(webhook_create_id)
update_ag_webhook = setup_oncall_webhook(
    "update", "status change", "PUT", update_endpoint,
    additional_data={
        "id": "{{{{ responses.{}.id }}}}".format(webhook_create_id),
    }
)
