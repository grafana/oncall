# Main
enabled = True
title = "(Legacy) Grafana Alerting"
slug = "legacy_grafana_alerting"
short_description = "Why I am legacy?"
is_displayed_on_web = True
is_featured = False
featured_tag_name = None
is_able_to_autoresolve = True
is_demo_alert_enabled = True
based_on_alertmanager = True

description = """ \
Alerts from Grafana Alertmanager are automatically routed to this integration.
{% for dict_item in grafana_alerting_entities %}
<br>Click <a href='{{dict_item.contact_point_url}}' target='_blank'>here</a>
 to open contact point, and
 <a href='{{dict_item.routes_url}}' target='_blank'>here</a>
 to open Notification policy for {{dict_item.alertmanager_name}} Alertmanager.
{% endfor %}
{% if not is_finished_alerting_setup %}
<br>Creating contact points and routes for other alertmanagers...
{% endif %}
"""

# Default templates
slack_title = """\
{# Usually title is located in payload.labels.alertname #}
{% set title = payload.get("labels", {}).get("alertname", "No title (check Web Title Template)") %}
{# Combine the title from different built-in variables into slack-formatted url #}
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}
"""

slack_message = """\
{{- payload.message }}
{%- if "status" in payload -%}
*Status*: {{ payload.status }}
{% endif -%}
*Labels:* {% for k, v in payload["labels"].items() %}
{{ k }}: {{ v }}{% endfor %}
*Annotations:* 
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as slack markdown url if it starts with http #}
{{ k }}: {% if v.startswith("http") %} <{{v}}|here> {% else %} {{v}} {% endif -%}
{% endfor %}
"""  # noqa:W291


slack_image_url = None

web_title = """\
{# Usually title is located in payload.labels.alertname #}
{{- payload.get("labels", {}).get("alertname", "No title (check Web Title Template)") }}
"""

web_message = """\
{{- payload.message }}
{%- if "status" in payload %}
**Status**: {{ payload.status }}
{% endif -%}
**Labels:** {% for k, v in payload["labels"].items() %}
*{{ k }}*: {{ v }}{% endfor %}
**Annotations:** 
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as markdown url if it starts with http #}
*{{ k }}*: {% if v.startswith("http") %} [here]({{v}}){% else %} {{v}} {% endif -%}
{% endfor %}
"""  # noqa:W291


web_image_url = slack_image_url

sms_title = '{{ payload.get("labels", {}).get("alertname", "Title undefined") }}'
phone_call_title = sms_title

telegram_title = sms_title

telegram_message = """\
{{- payload.messsage }}
{%- if "status" in payload -%}
<b>Status</b>: {{ payload.status }}
{% endif -%}
<b>Labels:</b> {% for k, v in payload["labels"].items() %}
{{ k }}: {{ v }}{% endfor %}
<b>Annotations:</b> 
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as markdown url if it starts with http #}
{{ k }}: {{ v }}
{% endfor %}"""  # noqa:W291

telegram_image_url = slack_image_url

source_link = "{{ payload.generatorURL }}"

grouping_id = web_title

resolve_condition = """\
{{ payload.get("status", "") == "resolved" }}
"""

acknowledge_condition = None

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
            "annotations": {"description": "This alert was sent by user for demonstration purposes"},
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
