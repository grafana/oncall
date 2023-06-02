# Main
enabled = True
title = "Zabbix"
slug = "zabbix"
short_description = None
description = None
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.get("title", "Title undefined (check Slack Title Template)") }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = '{{ payload.get("message", "") }}'

slack_image_url = '{{ payload.get("image_url", "") }}'

web_title = '{{ payload.get("title", "Title undefined (check Web Title Template)") }}'

web_message = slack_message

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = sms_title

telegram_title = sms_title

telegram_message = slack_message

telegram_image_url = slack_image_url

source_link = "{{ payload.link_to_upstream_details }}"

grouping_id = '{{ payload.get("alert_uid", "")}}'

resolve_condition = '{{ payload.get("state", "").upper() == "OK" }}'

acknowledge_condition = None

group_verbose_name = web_title

example_payload = {
    "alert_uid": "08d6891a-835c-e661-39fa-96b6a9e26552",
    "title": "TestAlert: The whole system is down",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
    "state": "alerting",
    "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
    "message": "This alert was sent by user for demonstration purposes\nSmth happened. Oh no!",
}
