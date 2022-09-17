# Main
enabled = True
title = "Webhook"
slug = "webhook"
short_description = None
description = None
is_featured = False
is_displayed_on_web = True
is_able_to_autoresolve = True
is_demo_alert_enabled = True

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} Incident>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}

"""

slack_message = "```{{ payload|tojson_pretty }}```"

slack_image_url = None

web_title = "Incident"

web_message = """\
```
{{ payload|tojson_pretty }}
```
"""

web_image_url = slack_image_url

sms_title = """\
{{ payload.message }}, 
Incident #
{{ grafana_oncall_incident_id }}, 
Organization: 
{{ grafana_oncall_organization }}, 
Alert channel: 
{{ integration_name }},
Link: 
{{ grafana_oncall_link }}

"""

phone_call_title = sms_title

email_title = web_title

email_message = "{{ payload|tojson_pretty }}"

telegram_title = sms_title

telegram_message = "<code>{{ payload|tojson_pretty }}</code>"

telegram_image_url = slack_image_url

source_link = "{{ payload.url }}"

grouping_id = "{{ payload }}"

resolve_condition = """\
{%- if "is_amixr_heartbeat_restored" in payload -%}
{# We don't know the payload format from your integration.  #}
{# The heartbeat alerts will go here so we check for our own key #}
{{ payload["is_amixr_heartbeat_restored"] }}
{%- else -%}
{{ payload.get("state", "").upper() == "OK" }}
{%- endif %}"""
acknowledge_condition = None

example_payload = {"message": "This alert was sent by user for the demonstration purposes"}
