# Main
enabled = True
title = "Direct paging"
slug = "direct_paging"
short_description = None
description = None
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = False
is_demo_alert_enabled = False

description = None

# Default templates
slack_title = """\
*<{{ grafana_oncall_link }}|#{{ grafana_oncall_incident_id }} {{ payload.oncall.title }}>* via {{ integration_name }}
{% if source_link %}
 (*<{{ source_link }}|source>*)
{% endif %}
"""

slack_message = """{{ payload.oncall.message }}

created by {{ payload.oncall.author_username }}
"""

slack_image_url = None

web_title = "{{ payload.oncall.title }}"

web_message = """{{ payload.oncall.message }}
{% if source_link %}
<{{ source_link }} | Link to the original message >
{% endif %}
created by {{ payload.oncall.author_username }}
"""

web_image_url = slack_image_url

sms_title = web_title

phone_call_title = sms_title

telegram_title = sms_title

telegram_message = slack_message

telegram_image_url = slack_image_url

source_link = "{{ payload.oncall.permalink }}"

grouping_id = """{{ payload }}"""

resolve_condition = None

acknowledge_condition = None

example_payload = None
