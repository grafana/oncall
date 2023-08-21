# Main
enabled = True
title = "Heartbeat"
slug = "heartbeat"
short_description = None
description = None
is_displayed_on_web = False
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.get("title", "Title undefined (check Slack Title Template)") }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

grouping_id = """\
{{ payload.get("id", "") }}{{ payload.get("user_defined_id", "") }}
"""

resolve_condition = '{{ payload.get("is_resolve", False) == True }}'

acknowledge_condition = None

example_payload = None
