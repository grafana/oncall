# Main
enabled = True
title = "Grafana Alerting"
slug = "grafana_alerting"
short_description = (
    "Your current Grafana Cloud stack. Automatically create an alerting contact point and a route in Grafana"
)
description = None
is_displayed_on_web = True
is_featured = True
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = """ \
Alerts from Grafana Alertmanager are automatically routed to this integration.
{% for dict_item in grafana_alerting_entities %}
<br>Click <a href='{{dict_item.contact_point_url}}' target='_blank'>here</a>
 to open contact point, and
 <a href='{{dict_item.routes_url}}' target='_blank'>here</a>
 to open routes for {{dict_item.alertmanager_name}} Alertmanager.
{% endfor %}
{% if not is_finished_alerting_setup %}
<br>Creating contact points and routes for other alertmanagers...
{% endif %}
"""

# Web
web_title = """{{- payload.get("labels", {}).get("alertname", "No title (check Title Template)") -}}"""
web_message = """\
{%- set annotations = payload.annotations.copy() -%}
{%- set labels = payload.labels.copy() -%}

{%- if "summary" in annotations %}
{{ annotations.summary }}
{%- set _ = annotations.pop('summary') -%}
{%- endif %}

{%- if "message" in annotations %}
{{ annotations.message }}
{%- set _ = annotations.pop('message') -%}
{%- endif %}

{% set severity = labels.severity | default("Unknown") -%}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)

{% if "runbook_url" in annotations -%}
[:book: Runbook:link:]({{ annotations.runbook_url }})
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
[:closed_book: Runbook (internal):link:]({{ annotations.runbook_url_internal }})
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

:label: Labels:
{%- for k, v in payload["labels"].items() %}
- {{ k }}: {{ v }}  
{%- endfor %}

{% if annotations | length > 0 -%}
:pushpin: Other annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}
"""  # noqa: W291

web_image_url = None

# Behaviour
source_link = "{{ payload.generatorURL }}"

grouping_id = web_title

resolve_condition = """{{ payload.status == "resolved" }}"""

acknowledge_condition = None

# Slack
slack_title = """\
{% set title = payload.get("labels", {}).get("alertname", "No title (check Title Template)") %}
{# Combine the title from different built-in variables into slack-formatted url #}
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}
"""

# default slack message template is identical to web message template, except urls
# It can be based on web message template (see example), but it can affect existing templates
# slack_message = """
# {% set mkdwn_link_regex = "\[([\w\s\d:]+)\]\((https?:\/\/[\w\d./?=#]+)\)" %}
# {{ web_message
#   | regex_replace(mkdwn_link_regex, "<\\2|\\1>")
# }}
# """

slack_message = """\
{%- set annotations = payload.annotations.copy() -%}
{%- set labels = payload.labels.copy() -%}

{%- if "summary" in annotations %}
{{ annotations.summary }}
{%- set _ = annotations.pop('summary') -%}
{%- endif %}

{%- if "message" in annotations %}
{{ annotations.message }}
{%- set _ = annotations.pop('message') -%}
{%- endif %}

{# Set oncall_slack_user_group to slack user group in the following format "@users-oncall" #}
{%- set oncall_slack_user_group = None -%}
{%- if oncall_slack_user_group %}
Heads up {{ oncall_slack_user_group }}
{%- endif %}

{% set severity = labels.severity | default("Unknown") -%}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)

{% if "runbook_url" in annotations -%}
<{{ annotations.runbook_url }}|:book: Runbook:link:>
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
<{{ annotations.runbook_url_internal }}|:closed_book: Runbook (internal):link:>
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

:label: Labels:
{%- for k, v in payload["labels"].items() %}
- {{ k }}: {{ v }}  
{%- endfor %}

{% if annotations | length > 0 -%}
:pushpin: Other annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}
"""  # noqa: W291

slack_image_url = None

# SMS
sms_title = web_title

# Phone
phone_call_title = web_title

# Telegram
telegram_title = web_title

# default telegram message template is identical to web message template, except urls
# It can be based on web message template (see example), but it can affect existing templates
# telegram_message = """
# {% set mkdwn_link_regex = "\[([\w\s\d:]+)\]\((https?:\/\/[\w\d./?=#]+)\)" %}
# {{ web_message
#   | regex_replace(mkdwn_link_regex, "<a href='\\2'>\\1</a>")
# }}
# """
telegram_message = """\
{%- set annotations = payload.annotations.copy() -%}
{%- set labels = payload.labels.copy() -%}

{%- if "summary" in annotations %}
{{ annotations.summary }}
{%- set _ = annotations.pop('summary') -%}
{%- endif %}

{%- if "message" in annotations %}
{{ annotations.message }}
{%- set _ = annotations.pop('message') -%}
{%- endif %}

{% set severity = labels.severity | default("Unknown") -%}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)

{% if "runbook_url" in annotations -%}
<a href='{{ annotations.runbook_url }}'>:book: Runbook:link:</a>
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
<a href='{{ annotations.runbook_url_internal }}'>:closed_book: Runbook (internal):link:</a>
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

:label: Labels:
{%- for k, v in payload["labels"].items() %}
- {{ k }}: {{ v }}  
{%- endfor %}

{% if annotations | length > 0 -%}
:pushpin: Other annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}
"""  # noqa: W291

telegram_image_url = None

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
