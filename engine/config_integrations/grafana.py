# Main
enabled = True
title = "Grafana"
slug = "grafana"
short_description = "Other grafana"
description = None
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = None

# Default templates
slack_title = """\
{# Usually title is located in payload.labels.alertname #}
{% set title = payload.get("title", "") or payload.get("labels", {}).get("alertname", "No title (check Web Title Template)") %}
{# Combine the title from different built-in variables into slack-formatted url #}
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}
"""

slack_message = """\
{{- payload.message }}
{%- for value in payload.get("evalMatches", []) %}
*{{ value.metric }}*: {{ value.value }}
{% endfor -%}
{%- if "status" in payload -%}
*Status*: {{ payload.status }}
{% endif -%}
{%- if "labels" in payload -%}
*Labels:* {% for k, v in payload["labels"].items() %}
{{ k }}: {{ v }}{% endfor %}
{% endif -%}
{%- if "annotations" in payload -%}
*Annotations:*
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as slack markdown url if it starts with http #}
{{ k }}: {% if v.startswith("http") %} <{{v}}|here> {% else %} {{v}} {% endif -%}
{% endfor %}
{%- endif -%}
"""

slack_image_url = """\
{{- payload.get(imageUrl) -}}
"""

web_title = """\
{# Usually title is located in payload.labels.alertname #}
{{- payload.get("title", "") or payload.get("labels", {}).get("alertname", "No title (check Web Title Template)") }}
"""

web_message = """\
{{- payload.message }}
{% for value in payload.get("evalMatches", []) -%}
**{{ value.metric }}**: {{ value.value }}
{% endfor %}
{%- if "status" in payload %}
**Status**: {{ payload.status }}
{% endif -%}
{%- if "labels" in payload -%}
**Labels:** {% for k, v in payload["labels"].items() %}
*{{ k }}*: {{ v }}{% endfor %}
{% endif -%}
{%- if "annotations" in payload -%}
**Annotations:**
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as markdown url if it starts with http #}
*{{ k }}*: {% if v.startswith("http") %} [here]({{v}}){% else %} {{v}} {% endif -%}
{% endfor %}
{% endif -%}
"""

web_image_url = slack_image_url

sms_title = """\
{{ payload.get("ruleName", "") or payload.get("labels", {}).get("alertname", "Title undefined") }}
"""

phone_call_title = sms_title

telegram_title = sms_title

telegram_message = """\
{{- payload.messsage }}
{%- for value in payload.get("evalMatches", []) %}
<b>{{ value.metric }}:</b> {{ value.value }}
{% endfor -%}
{%- if "status" in payload -%}
<b>Status</b>: {{ payload.status }}
{% endif -%}
{%- if "labels" in payload -%}
<b>Labels:</b> {% for k, v in payload["labels"].items() %}
{{ k }}: {{ v }}{% endfor %}
{% endif -%}
{%- if "annotations" in payload -%}
<b>Annotations:</b>
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as markdown url if it starts with http #}
{{ k }}: {{ v }}
{% endfor %}
{%- endif -%}
"""

telegram_image_url = slack_image_url

source_link = """\
{{ payload.get("ruleUrl", "") or payload.generatorURL }}
"""

grouping_id = """\
{{ payload.get("ruleName", "") or payload.get("labels", {}).get("alertname", "No title (check Web Title Template)") }}
"""

resolve_condition = """\
{{ payload.get("state") == "ok" or payload.get("status", "") == "resolved" }}
"""

acknowledge_condition = None

# Miscellaneous
example_payload = {
    "receiver": "amixr",
    "status": "firing",
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "alertname": "TestAlert",
                "region": "eu-1",
            },
            "annotations": {"description": "This alert was sent by user for the demonstration purposes"},
            "startsAt": "2018-12-25T15:47:47.377363608Z",
            "endsAt": "0001-01-01T00:00:00Z",
            "generatorURL": "",
            "amixr_demo": True,
        }
    ],
    "groupLabels": {},
    "commonLabels": {},
    "commonAnnotations": {},
    "externalURL": "http://f1d1ef51d710:9093",
    "version": "4",
    "groupKey": "{}:{}",
}
