# Main
enabled = True
title = "Maintenance"
slug = "maintenance"
short_description = None
description = None
is_displayed_on_web = False
is_featured = False
is_able_to_autoresolve = False
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.get("title", "Maintenance") }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = "{{ payload.message }}"

slack_image_url = "{{ payload.image_url }}"

web_title = '{{ payload.get("title", "Maintenance") }}'

web_message = slack_message

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = sms_title

telegram_title = sms_title

telegram_message = slack_message

telegram_image_url = slack_image_url

source_link = None

grouping_id = None

resolve_condition = None

acknowledge_condition = None

example_payload = None
