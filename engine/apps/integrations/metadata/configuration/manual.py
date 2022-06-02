# Main
enabled = True
title = "Manual"
slug = "manual"
short_description = None
description = None
is_displayed_on_web = False
is_featured = False
is_able_to_autoresolve = False
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """{% set metadata = payload.view.private_metadata %}
{%-if "message" in metadata -%}
{% set title = "Message from @" + metadata.author_username %}
{%- else -%}
{% set title = payload.view.state["values"].TITLE_INPUT.FinishCreateIncidentViewStep.value %}
{%- endif -%}
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{%- endif %}
"""

slack_message = """{% set metadata = payload.view.private_metadata %}
{% if "message" in metadata -%}
{{ metadata.message.text }}

<https://{{ payload.team.domain }}.slack.com/archives/{{ metadata.channel_id }}/{{ metadata.message.ts }} | Original message... >
{%- else -%}
{{ payload.view.state["values"].MESSAGE_INPUT.FinishCreateIncidentViewStep.value }}

created by {{ payload.user.name }}
{%- endif -%}"""

slack_image_url = None

web_title = """{% set metadata = payload.view.private_metadata %}
{%-if "message" in metadata -%}
{{ "Message from @" + metadata.author_username }}
{%- else -%}
{{ payload.view.state["values"].TITLE_INPUT.FinishCreateIncidentViewStep.value }}
{%- endif -%}"""

web_message = slack_message

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = sms_title

email_title = web_title

email_message = slack_message

telegram_title = sms_title

telegram_message = slack_message

telegram_image_url = slack_image_url

source_link = """\
{% set metadata = payload.view.private_metadata %}
{%- if "message" in metadata %}
https://{{ payload.team.domain }}.slack.com/archives/{{ payload.channel.id }}/{{ payload.message.ts }}
{% endif -%}"""

grouping_id = """{{ payload }}"""

resolve_condition = None

acknowledge_condition = None

group_verbose_name = web_title
