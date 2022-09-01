# Main
enabled = True
title = "AlertManager"
slug = "alertmanager"
short_description = "Prometheus"
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = """
Alerts from Grafana Alertmanager are automatically routed to this integration."
{% for dict_item in grafana_alerting_entities %}
<br>Click <a href='{{dict_item.contact_point_url}}' target='_blank'>here</a>
 to open contact point, and
 <a href='{{dict_item.routes_url}}' target='_blank'>here</a>
 to open routes for {{dict_item.alertmanager_name}} Alertmanager.
{% endfor %}
{% if not is_finished_alerting_setup %}
<br>Creating contact points and routes for other alertmanagers...
{% endif %}"""

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
"""  # noqa: W291


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
"""  # noqa: W291


web_image_url = slack_image_url

sms_title = '{{ payload.get("labels", {}).get("alertname", "Title undefined") }}'
phone_call_title = sms_title

email_title = web_title

email_message = """\
{{- payload.messsage }}
{%- if "status" in payload -%}
**Status**: {{ payload.status }}
{% endif -%}
**Labels:** {% for k, v in payload["labels"].items() %}
{{ k }}: {{ v }}{% endfor %}
**Annotations:** 
{%- for k, v in payload.get("annotations", {}).items() %}
{#- render annotation as markdown url if it starts with http #}
{{ k }}: {{v}}
{% endfor %}
"""  # noqa: W291

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
{% endfor %}"""  # noqa: W291

telegram_image_url = slack_image_url

source_link = "{{ payload.generatorURL }}"

grouping_id = "{{ payload.labels }}"

resolve_condition = """\
{{ payload.get("status", "") == "resolved" }}
"""

acknowledge_condition = None

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
        "message": (
            "*Status*: firing\n"
            "*Labels:* \n"
            "job: kube-state-metrics\n"
            "instance: 10.143.139.7:8443\n"
            "job_name: email-tracking-perform-initialization-1.0.50\n"
            "severity: warning\n"
            "alertname: KubeJobCompletion\n"
            "namespace: default\n"
            "prometheus: monitoring/k8s\n"
            "*Annotations:*\n"
            "message:  Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete. \n"
            "runbook_url:  <https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion|here> "
        ),
        "image_url": None,
    },
    "web": {
        "title": "KubeJobCompletion",
        "message": (
            "<p>"
            "<strong>Status</strong>: firing<br/>"
            "<strong>Labels:</strong> <br/>"
            "<em>job</em>: kube-state-metrics<br/>"
            "<em>instance</em>: 10.143.139.7:8443<br/>"
            "<em>job_name</em>: email-tracking-perform-initialization-1.0.50<br/>"
            "<em>severity</em>: warning<br/><em>alertname</em>: KubeJobCompletion<br/>"
            "<em>namespace</em>: default<br/><em>prometheus</em>: monitoring/k8s<br/>"
            "<strong>Annotations:</strong><br/>"
            "<em>message</em>:  Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete. <br/>"
            "<em>runbook_url</em>:  "
            '<a href="https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion">here</a>'
            "</p>"
        ),
        "image_url": None,
    },
    "sms": {
        "title": "KubeJobCompletion",
    },
    "phone_call": {
        "title": "KubeJobCompletion",
    },
    "email": {
        "title": "KubeJobCompletion",
        "message": (
            "**Status**: firing\n"
            "**Labels:** \n"
            "job: kube-state-metrics\n"
            "instance: 10.143.139.7:8443\n"
            "job_name: email-tracking-perform-initialization-1.0.50\n"
            "severity: warning\n"
            "alertname: KubeJobCompletion\n"
            "namespace: default\n"
            "prometheus: monitoring/k8s\n"
            "**Annotations:**\n"
            "message: Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.\n\n"
            "runbook_url: https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion\n"
        ),
    },
    "telegram": {
        "title": "KubeJobCompletion",
        "message": (
            "<b>Status</b>: firing\n"
            "<b>Labels:</b> \n"
            "job: kube-state-metrics\n"
            "instance: 10.143.139.7:8443\n"
            "job_name: email-tracking-perform-initialization-1.0.50\n"
            "severity: warning\n"
            "alertname: KubeJobCompletion\n"
            "namespace: default\n"
            "prometheus: monitoring/k8s\n"
            "<b>Annotations:</b>\n"
            "message: Job default/email-tracking-perform-initialization-1.0.50 is taking more than one hour to complete.\n\n"
            "runbook_url: https://github.com/kubernetes-monitoring/kubernetes-mixin/tree/master/runbook.md#alert-name-kubejobcompletion\n"
        ),
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
