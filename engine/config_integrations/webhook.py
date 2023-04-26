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

web_title = "{{ payload.get('title', 'Title unknown (Change integration web title template)') }}"
web_message = """\
```
{{ payload|tojson_pretty }}
```
"""
web_image_url = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ web_title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}

"""

slack_message = "```{{ payload|tojson_pretty }}```"

slack_image_url = None

sms_title = "{{ web_title }}"

phone_call_title = "{{ web_title }}"

telegram_title = "{{ web_title }}"

telegram_message = "<code>{{ payload|tojson_pretty }}</code>"

telegram_image_url = None

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
