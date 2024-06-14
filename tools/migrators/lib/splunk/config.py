import os

from lib.base_config import *  # noqa: F401,F403

SPLUNK_API_ID = os.environ["SPLUNK_API_ID"]
SPLUNK_API_KEY = os.environ["SPLUNK_API_KEY"]

SPLUNK_TO_ONCALL_CONTACT_METHOD_MAP = {
    "sms": "notify_by_sms",
    "phone": "notify_by_phone_call",
    "email": "notify_by_email",
    "push": "notify_by_mobile_app",
}

# NOTE: currently we only support `rotation_group` and `user`
UNSUPPORTED_ESCALATION_POLICY_EXECUTION_TYPES = [
    "email",
    "webhook",
    "policy_routing",
    "rotation_group_next",
    "rotation_group_previous",
    "team_page",
]
