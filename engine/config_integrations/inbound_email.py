from django.conf import settings

# Main
enabled = True
title = "Inbound Email"
slug = "inbound_email"
short_description = None
description = None
is_displayed_on_web = settings.FEATURE_INBOUND_EMAIL_ENABLED
is_featured = False
is_able_to_autoresolve = False
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.get("title", "Title undefined (check Slack Title Template)") }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}"""

slack_message = "{{ payload.message }}"

slack_image_url = "{{ payload.image_url }}"

web_title = '{{ payload.get("title", "Title undefined (check Web Title Template)") }}'

web_message = slack_message

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = web_title

telegram_title = sms_title

telegram_message = slack_message

telegram_image_url = slack_image_url

source_link = "{{ payload.link_to_upstream_details }}"

grouping_id = '{{ payload.get("title", "")}}'

resolve_condition = '{{ payload.get("state", "").upper() == "OK" }}'

acknowledge_condition = None
