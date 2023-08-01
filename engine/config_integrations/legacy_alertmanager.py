# Main
enabled = True
title = "(Legacy) AlertManager"
slug = "legacy_alertmanager"
short_description = "Prometheus"
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True
based_on_alertmanager = True

description = None

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

grouping_id = "{{ payload.labels }}"

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

{# Optionally set oncall_slack_user_group to slack user group in the following format "@users-oncall" #}
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

tests = {
    "payload": {
        "endsAt": "0001-01-01T00:00:00Z",
        "labels": {
            "job": "kube-state-metrics",
            "instance": "10.143.139.7:8443",
            "job_name": "email-tracking-perform-initialization-1.0.50",
            "severity": "warning",
            "alertname": "KubeJobCompletion",
            "namespace": "default",
            "prometheus": "monitoring/k8s",
        },
        "status": "firing",
        "startsAt": "2019-12-13T08:57:35.095800493Z",
        "annotations": {
            "message": "Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.",
            "runbook_url": "https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion",
        },
        "generatorURL": (
            "https://localhost/prometheus/graph?g0.expr=kube_job_spec_completions%7Bjob%3D%22kube-state-metrics%22%7D"
            "+-+kube_job_status_succeeded%7Bjob%3D%22kube-state-metrics%22%7D+%3E+0&g0.tab=1"
        ),
    },
    "slack": {
        "title": (
            "*<{web_link}|#1 KubeJobCompletion>* via {integration_name} "
            "(*<"
            "https://localhost/prometheus/graph?g0.expr=kube_job_spec_completions%7Bjob%3D%22kube-state-metrics%22%7D"
            "+-+kube_job_status_succeeded%7Bjob%3D%22kube-state-metrics%22%7D+%3E+0&g0.tab=1"
            "|source>*)"
        ),
        "message": "\nJob default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.\n\n\n\nSeverity: warning :warning:\nStatus: firing :fire: (on the source)\n\n<https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion|:book: Runbook:link:>\n\n:label: Labels:\n- job: kube-state-metrics\n- instance: 10.143.139.7:8443\n- job_name: email-tracking-perform-initialization-1.0.50\n- severity: warning\n- alertname: KubeJobCompletion\n- namespace: default\n- prometheus: monitoring/k8s\n\n",  # noqa
        "image_url": None,
    },
    "web": {
        "title": "KubeJobCompletion",
        "message": '<p>Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.  </p>\n<p>Severity: warning ⚠️ <br/>\nStatus: firing 🔥 (on the source)  </p>\n<p><a href="https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion" rel="nofollow noopener" target="_blank">📖 Runbook🔗</a> </p>\n<p>🏷️ Labels:  </p>\n<ul>\n<li>job: kube-state-metrics  </li>\n<li>instance: 10.143.139.7:8443  </li>\n<li>job_name: email-tracking-perform-initialization-1.0.50  </li>\n<li>severity: warning  </li>\n<li>alertname: KubeJobCompletion  </li>\n<li>namespace: default  </li>\n<li>prometheus: monitoring/k8s  </li>\n</ul>',  # noqa
        "image_url": None,
    },
    "sms": {
        "title": "KubeJobCompletion",
    },
    "phone_call": {
        "title": "KubeJobCompletion",
    },
    "telegram": {
        "title": "KubeJobCompletion",
        "message": "\nJob default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.\n\nSeverity: warning ⚠️\nStatus: firing 🔥 (on the source)\n\n<a href='https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion'>📖 Runbook🔗</a>\n\n🏷️ Labels:\n- job: kube-state-metrics\n- instance: 10.143.139.7:8443\n- job_name: email-tracking-perform-initialization-1.0.50\n- severity: warning\n- alertname: KubeJobCompletion\n- namespace: default\n- prometheus: monitoring/k8s\n\n",  # noqa
        "image_url": None,
    },
}

# Misc
example_payload = {
    "receiver": "amixr",
    "status": "firing",
    "alerts": [
        {
            "status": "firing",
            "labels": {"alertname": "TestAlert", "region": "eu-1", "severity": "critical"},
            "annotations": {
                "message": "This is test alert",
                "description": "This alert was sent by user for demonstration purposes",
                "runbook_url": "https://grafana.com/",
            },
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
