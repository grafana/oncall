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
featured_tag_name = "Quick Connect"
is_able_to_autoresolve = True
is_demo_alert_enabled = True
based_on_alertmanager = True


# Behaviour
source_link = "{{ payload.externalURL }}"

grouping_id = "{{ payload.groupKey }}"

resolve_condition = """{{ payload.status == "resolved" }}"""

acknowledge_condition = None

# Web
web_title = """\
{% set groupLabels = payload.get("groupLabels", {}).copy() -%}
{% if "labels" in payload -%}
{# backward compatibility with legacy alertmanager integration -#}
{% set alertname = payload.get("labels", {}).get("alertname", "") -%} 
{% else -%}
{% set alertname = groupLabels.pop("alertname", "")  -%}
{% endif -%}

[{{ payload.status }}{% if payload.status == 'firing' and payload.numFiring %}:{{ payload.numFiring }}{% endif %}] {{ alertname }} {% if groupLabels | length > 0 %}({{ groupLabels.values()|join(", ") }}){% endif %}
"""  # noqa

web_message = """\
{% set annotations = payload.get("commonAnnotations", {}).copy() -%}
{% set groupLabels = payload.get("groupLabels", {}) -%}
{% set commonLabels = payload.get("commonLabels", {}) -%}
{% set severity = groupLabels.severity -%}
{% set legacyLabels = payload.get("labels", {}) -%}
{% set legacyAnnotations = payload.get("annotations", {}) -%}

{% if severity -%}
{% set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif -%}

{% set status = payload.get("status", "Unknown") -%}
{% set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") -%}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.numFiring -%}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif -%}

{% if "runbook_url" in annotations -%}
[:book: Runbook:link:]({{ annotations.runbook_url }})
{% set _ = annotations.pop('runbook_url') -%}
{% endif -%}

{% if "runbook_url_internal" in annotations -%}
[:closed_book: Runbook (internal):link:]({{ annotations.runbook_url_internal }})
{% set _ = annotations.pop('runbook_url_internal') -%}
{% endif %}

{%- if groupLabels | length > 0 %}
GroupLabels:
{% for k, v in groupLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if commonLabels | length > 0 -%}
CommonLabels:
{% for k, v in commonLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if annotations | length > 0 -%}
Annotations:
{% for k, v in annotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{# backward compatibility with legacy alertmanager integration -#}
{% if legacyLabels | length > 0 -%}
Labels:
{% for k, v in legacyLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if legacyAnnotations | length > 0 -%}
Annotations:
{% for k, v in legacyAnnotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}
[View in AlertManager]({{ source_link }})
"""


# Slack
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ web_title }}>* via {{ integration_name }}
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
{% set annotations = payload.get("commonAnnotations", {}).copy() -%}
{% set groupLabels = payload.get("groupLabels", {}) -%}
{% set commonLabels = payload.get("commonLabels", {}) -%}
{% set severity = groupLabels.severity -%}
{% set legacyLabels = payload.get("labels", {}) -%}
{% set legacyAnnotations = payload.get("annotations", {}) -%}

{% if severity -%}
{% set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif -%}

{% set status = payload.get("status", "Unknown") -%}
{% set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") -%}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.numFiring -%}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif -%}

{% if "runbook_url" in annotations -%}
<{{ annotations.runbook_url }}|:book: Runbook:link:>
{% set _ = annotations.pop('runbook_url') -%}
{% endif -%}

{% if "runbook_url_internal" in annotations -%}
<{{ annotations.runbook_url_internal }}|:closed_book: Runbook (internal):link:>
{% set _ = annotations.pop('runbook_url_internal') -%}
{% endif %}

{%- if groupLabels | length > 0 %}
GroupLabels:
{% for k, v in groupLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if commonLabels | length > 0 -%}
CommonLabels:
{% for k, v in commonLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if annotations | length > 0 -%}
Annotations:
{% for k, v in annotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{# backward compatibility with legacy alertmanager integration -#}
{% if legacyLabels | length > 0 -%}
Labels:
{% for k, v in legacyLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if legacyAnnotations | length > 0 -%}
Annotations:
{% for k, v in legacyAnnotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}
"""
# noqa: W291


slack_image_url = None

web_image_url = None

# SMS
sms_title = web_title

# Phone
phone_call_title = """{{ payload.get("groupLabels", {}).values() |join(", ") }}"""

# Telegram
telegram_title = web_title

telegram_message = """\
{% set annotations = payload.get("commonAnnotations", {}).copy() -%}
{% set groupLabels = payload.get("groupLabels", {}) -%}
{% set commonLabels = payload.get("commonLabels", {}) -%}
{% set severity = groupLabels.severity -%}
{% set legacyLabels = payload.get("labels", {}) -%}
{% set legacyAnnotations = payload.get("annotations", {}) -%}

{% if severity -%}
{% set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif -%}

{% set status = payload.get("status", "Unknown") -%}
{% set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") -%}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.numFiring -%}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif -%}

{% if "runbook_url" in annotations -%}
<a href='{{ annotations.runbook_url }}'>:book: Runbook:link:</a>
{% set _ = annotations.pop('runbook_url') -%}
{% endif -%}

{% if "runbook_url_internal" in annotations -%}
<a href='{{ annotations.runbook_url_internal }}'>:closed_book: Runbook (internal):link:</a>
{% set _ = annotations.pop('runbook_url_internal') -%}
{% endif %}

{%- if groupLabels | length > 0 %}
GroupLabels:
{% for k, v in groupLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if commonLabels | length > 0 -%}
CommonLabels:
{% for k, v in commonLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if annotations | length > 0 -%}
Annotations:
{% for k, v in annotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{# backward compatibility with legacy alertmanager integration -#}
{% if legacyLabels | length > 0 -%}
Labels:
{% for k, v in legacyLabels.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}

{% if legacyAnnotations | length > 0 -%}
Annotations:
{% for k, v in legacyAnnotations.items() -%}
- {{ k }}: {{ v }}
{% endfor %}
{% endif -%}
<a href='{{ source_link }}'>View in AlertManager</a>
"""

telegram_image_url = None


example_payload = {
    "alerts": [
        {
            "endsAt": "0001-01-01T00:00:00Z",
            "labels": {
                "job": "node",
                "group": "production",
                "instance": "localhost:8081",
                "severity": "critical",
                "alertname": "InstanceDown",
            },
            "status": "firing",
            "startsAt": "2023-06-12T08:24:38.326Z",
            "annotations": {
                "title": "Instance localhost:8081 down",
                "description": "localhost:8081 of job node has been down for more than 1 minute.",
            },
            "fingerprint": "f404ecabc8dd5cd7",
            "generatorURL": "",
        },
        {
            "endsAt": "0001-01-01T00:00:00Z",
            "labels": {
                "job": "node",
                "group": "canary",
                "instance": "localhost:8082",
                "severity": "critical",
                "alertname": "InstanceDown",
            },
            "status": "firing",
            "startsAt": "2023-06-12T08:24:38.326Z",
            "annotations": {
                "title": "Instance localhost:8082 down",
                "description": "localhost:8082 of job node has been down for more than 1 minute.",
            },
            "fingerprint": "f8f08d4e32c61a9d",
            "generatorURL": "",
        },
        {
            "endsAt": "0001-01-01T00:00:00Z",
            "labels": {
                "job": "node",
                "group": "production",
                "instance": "localhost:8083",
                "severity": "critical",
                "alertname": "InstanceDown",
            },
            "status": "firing",
            "startsAt": "2023-06-12T08:24:38.326Z",
            "annotations": {
                "title": "Instance localhost:8083 down",
                "description": "localhost:8083 of job node has been down for more than 1 minute.",
            },
            "fingerprint": "39f38c0611ee7abd",
            "generatorURL": "",
        },
    ],
    "status": "firing",
    "version": "4",
    "groupKey": '{}:{alertname="InstanceDown"}',
    "receiver": "combo",
    "numFiring": 3,
    "externalURL": "",
    "groupLabels": {"alertname": "InstanceDown"},
    "numResolved": 0,
    "commonLabels": {"job": "node", "severity": "critical", "alertname": "InstanceDown"},
    "truncatedAlerts": 0,
    "commonAnnotations": {},
}
