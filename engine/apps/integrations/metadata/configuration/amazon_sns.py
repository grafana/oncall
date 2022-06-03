# Main
enabled = True
title = "Amazon SNS"
slug = "amazon_sns"
short_description = None
is_displayed_on_web = True
description = None
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True

description = None

# Default templates
slack_title = """\
{% if payload|length == 0 -%}
{% set title = payload.get("AlarmName", "Alert") %}
{%- else -%}
{% set title = "Alert" %}
{%- endif %}

*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = """\
{% if payload|length == 1 and "message" in payload -%}
{{ payload.get("message", "Non-JSON payload received. Please make sure you publish monitoring Alarms to SNS, not logs: https://docs.amixr.io/#/integrations/amazon_sns") }}
{%- else -%}
*State* {{ payload.get("NewStateValue", "NO") }}
Region: {{ payload.get("Region", "Undefined") }}
_Description_: {{ payload.get("AlarmDescription", "Undefined") }}
{%- endif %}
"""

slack_image_url = None

web_title = """\
{% if payload|length == 0 -%}
{{ payload.get("AlarmName", "Alert")}}
{%- else -%}
Alert
{%- endif %}"""

web_message = """\
{% if payload|length == 1 and "message" in payload -%}
{{ payload.get("message", "Non-JSON payload received. Please make sure you publish monitoring Alarms to SNS, not logs: https://docs.amixr.io/#/integrations/amazon_sns") }}
{%- else -%}
**State** {{ payload.get("NewStateValue", "NO") }}
Region: {{ payload.get("Region", "Undefined") }}
*Description*: {{ payload.get("AlarmDescription", "Undefined") }}
{%- endif %}
"""

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = web_title

email_title = web_title

email_message = "{{ payload|tojson_pretty }}"

telegram_title = sms_title

telegram_message = """\
{% if payload|length == 1 and "message" in payload -%}
{{ payload.get("message", "Non-JSON payload received. Please make sure you publish monitoring Alarms to SNS, not logs: https://docs.amixr.io/#/integrations/amazon_sns") }}
{%- else -%}
<b>State</b> {{ payload.get("NewStateValue", "NO") }}
Region: {{ payload.get("Region", "Undefined") }}
<i>Description</i>: {{ payload.get("AlarmDescription", "Undefined") }}
{%- endif %}
"""

telegram_image_url = slack_image_url

source_link = """\
{% if payload|length == 0 -%}
{% if payload.get("Trigger", {}).get("Namespace") == "AWS/ElasticBeanstalk" -%}
https://console.aws.amazon.com/elasticbeanstalk/home?region={{ payload.get("TopicArn").split(":")[3] }}
{%- else -%}
https://console.aws.amazon.com/cloudwatch//home?region={{ payload.get("TopicArn").split(":")[3] }}
{%- endif %}
{%- endif %}"""

grouping_id = web_title

resolve_condition = """\
{{ payload.get("NewStateValue", "") == "OK" }}
"""

acknowledge_condition = None

group_verbose_name = web_title

example_payload = {"foo": "bar"}
