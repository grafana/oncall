import json
import requests

# having setup a Discord webhook for a channel, this script will 
# setup OnCall webhooks to send and update notifications for alert group created/updated triggers

# Configuration
ONCALL_API_BASE_URL = "https://oncall-prod-us-central-0.grafana.net/oncall"
ONCALL_TOKEN = "<oncall API token>"
ONCALL_WEBHOOK_PREFIX = "discord"  # prefix for webhooks naming
DISCORD_WEBHOOK_URL = "<discord webhook URL>"

NOTIFICATION_TEMPLATE = """
{% if alert_group.state == 'acknowledged'%}:orange_circle:{% elif alert_group.state == 'resolved'%}:green_circle:{% elif alert_group.state == 'silenced'%}:white_circle:{% else %}:red_circle:{% endif %} **{{ alert_group.title }}**
*{{ alert_group.state }}*
{{ alert_payload.message }}
*{{ integration.name }}*

{% if event.type == 'acknowledge' %}**Acknowledged by: {{ user.username }}**{% endif %}{% if event.type == 'resolve' %}**Resolved by: {{ user.username }}**{% endif %}{% if event.type == 'silence' %}**Silenced by: {{ user.username }} (until {{ event.until }})**{% endif %}

[View in Grafana OnCall]({{ alert_group.permalinks.web }})
"""

# --- Do not edit below this line ---

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
    url = "{}{}".format(DISCORD_WEBHOOK_URL, endpoint)
    data = {"content": NOTIFICATION_TEMPLATE}
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


# setup webhook for new alert group
endpoint = "?wait=true"
new_ag_webhook = setup_oncall_webhook("new", "alert group created", "POST", endpoint)

# setup webhook for status changes
webhook_create_id = new_ag_webhook.json()["id"]
update_endpoint = "/messages/{{{{ responses.{}.id }}}}".format(webhook_create_id)
update_ag_webhook = setup_oncall_webhook("update", "status change", "PATCH", update_endpoint)
