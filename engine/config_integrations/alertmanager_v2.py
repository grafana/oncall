# Main
enabled = True
title = "AlertManagerV2"
slug = "alertmanager_v2"
short_description = "Prometheus"
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True
description = None


# Behaviour
source_link = "{{ payload.externalURL }}"

grouping_id = "{{ payload.groupKey }}"

resolve_condition = """{{ payload.status == "resolved" }}"""

acknowledge_condition = None


web_title = """\
{%- set groupLabels = payload.groupLabels.copy() -%}
{%- set alertname = groupLabels.pop('alertname') | default("") -%}


[{{ payload.status }}{% if payload.status == 'firing' %}:{{ payload.numFiring }}{% endif %}] {{ alertname }} {% if groupLabels | length > 0 %}({{ groupLabels|join(", ") }}){% endif %}
"""  # noqa

web_message = """\
{%- set annotations = payload.commonAnnotations.copy() -%}

{% set severity = payload.groupLabels.severity -%}
{% if severity %}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif %}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.truncated_alerts == 0 %}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif %}

{% if "runbook_url" in annotations -%}
[:book: Runbook:link:]({{ annotations.runbook_url }})
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
[:closed_book: Runbook (internal):link:]({{ annotations.runbook_url_internal }})
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

GroupLabels:
{%- for k, v in payload["groupLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}

{% if payload["commonLabels"] | length > 0 -%}
CommonLabels:
{%- for k, v in payload["commonLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}

{% if annotations | length > 0 -%}
Annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}

[View in AlertManager]({{ source_link }})
"""


# Slack templates
slack_title = """\
{%- set groupLabels = payload.groupLabels.copy() -%}
{%- set alertname = groupLabels.pop('alertname') | default("") -%}
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
{%- set annotations = payload.commonAnnotations.copy() -%}

{% set severity = payload.groupLabels.severity -%}
{% if severity %}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif %}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.truncated_alerts == 0 %}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif %}

{% if "runbook_url" in annotations -%}
<{{ annotations.runbook_url }}|:book: Runbook:link:>
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
<{{ annotations.runbook_url_internal }}|:closed_book: Runbook (internal):link:>
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

GroupLabels:
{%- for k, v in payload["groupLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}

{% if payload["commonLabels"] | length > 0 -%}
CommonLabels:
{%- for k, v in payload["commonLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}

{% if annotations | length > 0 -%}
Annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}
"""
# noqa: W291


slack_image_url = None

web_image_url = None

sms_title = web_title


phone_call_title = """{{ payload.groupLabels|join(", ") }}"""

telegram_title = web_title

telegram_message = """\
{%- set annotations = payload.commonAnnotations.copy() -%}

{% set severity = payload.groupLabels.severity -%}
{% if severity %}
{%- set severity_emoji = {"critical": ":rotating_light:", "warning": ":warning:" }[severity] | default(":question:") -%}
Severity: {{ severity }} {{ severity_emoji }}
{% endif %}

{%- set status = payload.status | default("Unknown") %}
{%- set status_emoji = {"firing": ":fire:", "resolved": ":white_check_mark:"}[status] | default(":warning:") %}
Status: {{ status }} {{ status_emoji }} (on the source)
{% if status == "firing" and payload.truncated_alerts == 0 %}
Firing alerts – {{ payload.numFiring }}
Resolved alerts – {{ payload.numResolved }}
{% endif %}

{% if "runbook_url" in annotations -%}
<a href='{{ annotations.runbook_url }}'>:book: Runbook:link:</a>
{%- set _ = annotations.pop('runbook_url') -%}
{%- endif %}

{%- if "runbook_url_internal" in annotations -%}
<a href='{{ annotations.runbook_url_internal }}'>:closed_book: Runbook (internal):link:</a>
{%- set _ = annotations.pop('runbook_url_internal') -%}
{%- endif %}

GroupLabels:
{%- for k, v in payload["groupLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}

{% if payload["commonLabels"] | length > 0 -%}
CommonLabels:
{%- for k, v in payload["commonLabels"].items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}

{% if annotations | length > 0 -%}
Annotations:
{%- for k, v in annotations.items() %}
- {{ k }}: {{ v }}
{%- endfor %}
{% endif %}

<a href='{{ source_link }}'>View in AlertManager</a>
"""

telegram_image_url = None
