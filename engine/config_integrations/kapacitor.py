# Main
enabled = True
title = "Kapacitor"
slug = "kapacitor"
short_description = "InfluxDB"
description = None
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.get("id", "Title undefined (check Slack Title Template)") }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = """\
```{{ payload|tojson_pretty }}```
"""

slack_image_url = None

web_title = '{{ payload.get("id", "Title undefined (check Web Title Template)") }}'

web_message = """\
```
{{ payload|tojson_pretty }}
```
"""

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = web_title

telegram_title = sms_title

telegram_message = "<code>{{ payload|tojson_pretty }}</code>"

telegram_image_url = slack_image_url

source_link = None

grouping_id = '{{ payload.get("id", "") }}'

resolve_condition = '{{ payload.get("level", "").startswith("OK") }}'

acknowledge_condition = None

example_payload = {
    "id": "TestAlert",
    "message": "This alert was sent by user for demonstration purposes",
    "data": "{foo: bar}",
}
