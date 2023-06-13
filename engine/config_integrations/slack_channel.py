# Main
enabled = True
title = "Slack Channel"
slug = "slack_channel"
short_description = None
description = None
is_displayed_on_web = False
is_featured = False
is_able_to_autoresolve = False
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """\
{% if source_link -%}
*<{{ source_link }}|<#{{ payload.get("channel", "") }}>>*
{%- else -%}
<#{{ payload.get("channel", "") }}>
{%- endif %}"""

web_title = """\
{% if source_link -%}
[#{{ grafana_oncall_incident_id }}]{{ source_link }}) <#{{ payload.get("channel", "") }}>>*
{%- else -%}
*#{{ grafana_oncall_incident_id }}* <#{{ payload.get("channel", "") }}>
{%- endif %}"""

telegram_title = """\
{% if source_link -%}
<a href="{{ source_link }}">#{{ grafana_oncall_incident_id }}</a> {{ payload.get("channel", "") }}
{%- else -%}
*#{{ grafana_oncall_incident_id }}* <#{{ payload.get("channel", "") }}>
{%- endif %}"""

grouping_id = '{{ payload.get("ts", "") }}'

resolve_condition = None

acknowledge_condition = None

source_link = '{{ payload.get("amixr_mixin", {}).get("permalink", "")}}'

example_payload = None
