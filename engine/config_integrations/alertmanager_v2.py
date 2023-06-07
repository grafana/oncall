# Main
enabled = True
title = "AlertManagerV2"
slug = "alertmanagerV2"
short_description = "Prometheus"
is_displayed_on_web = True
is_featured = False
is_able_to_autoresolve = True
is_demo_alert_enabled = True


description = """description"""

# Default templates
slack_title = """slack title"""

slack_message = """slack message"""  # noqa: W291


slack_image_url = None


web_title = """\
[{{ payload.status }}{% if payload.status == 'firing' %}:{{ payload.num_firing }}{% endif %}] {{ payload.commonLabels["alertname"]}} ({% for k, v in payload["groupLabels"].items() if k != "alertname" %}{{ v }} {% endfor %}{% for k, v in payload["commonLabels"].items() if k != "alertname" and k not in payload["groupLabels"]%}{{ v }} {% endfor %})
"""

web_message = """\
**Firing**: {{ payload.num_firing }}
**Resolved**: {{ payload.num_resolved }}
**Group Labels:** {% for k, v in payload["groupLabels"].items() %}
*{{ k }}*: {{ v }}{% endfor %}
**Common Labels:** {% for k, v in payload["commonLabels"].items() %}
*{{ k }}*: {{ v }}{% endfor %}
**Common Annotations:** {% for k, v in payload["commonAnnotations"].items() %}
*{{ k }}*: {{ v }}{% endfor %}

[View in AlertManager]({{ payload.externalURL }})
"""


web_image_url = None

sms_title = web_title
phone_call_title = sms_title

telegram_title = "telegram title"

telegram_message = """telegram message"""  # noqa: W291

telegram_image_url = slack_image_url

source_link = "{{ payload.externalURL }}"

grouping_id = "{{ payload.groupKey }}"

resolve_condition = """{{ payload.status == "resolved" }}"""


acknowledge_condition = None
