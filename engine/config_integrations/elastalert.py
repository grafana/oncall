# Main
enabled = True
title = "Elastalert"
slug = "elastalert"
short_description = "Elastic"
is_displayed_on_web = True
description = None
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} Incident>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = "```{{ payload|tojson_pretty }}```"

slack_image_url = None

web_title = "Incident"

web_message = """\
```
{{ payload|tojson_pretty }}
```
"""

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = sms_title

telegram_title = sms_title

telegram_message = "<code>{{ payload|tojson_pretty }}</code>"

telegram_image_url = slack_image_url

source_link = None

grouping_id = '{{ payload.get("alert_uid", "")}}'

resolve_condition = """{{ payload.get("state", "").upper() == "OK" }}"""

acknowledge_condition = None

example_payload = {"message": "This alert was sent by user for demonstration purposes"}
