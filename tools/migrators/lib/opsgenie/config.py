import os

from lib.base_config import *  # noqa: F401,F403

OPSGENIE_API_KEY = os.environ["OPSGENIE_API_KEY"]
OPSGENIE_API_URL = os.getenv("OPSGENIE_API_URL", "https://api.opsgenie.com/v2")

OPSGENIE_TO_ONCALL_CONTACT_METHOD_MAP = {
    "sms": "notify_by_sms",
    "voice": "notify_by_phone_call",
    "email": "notify_by_email",
    "mobile": "notify_by_mobile_app",
}

OPSGENIE_TO_ONCALL_VENDOR_MAP = {
    "Datadog": "datadog",
    "Pingdom": "pingdom",
    "Prometheus": "alertmanager",
    "PRTG": "prtg",
    "Google Stackdriver": "stackdriver",
    "UptimeRobot": "uptimerobot",
    "New Relic": "newrelic",
    "Zabbix": "zabbix",
    "Elastic": "elastalert",
    "Firebase": "fabric",
    "Amazon CloudWatch": "amazon_sns",
}

# Set to true to migrate unsupported integrations to OnCall webhook integration
UNSUPPORTED_INTEGRATION_TO_WEBHOOKS = (
    os.getenv("UNSUPPORTED_INTEGRATION_TO_WEBHOOKS", "false").lower() == "true"
)

MIGRATE_USERS = os.getenv("MIGRATE_USERS", "true").lower() == "true"

# Filter resources by team
OPSGENIE_FILTER_TEAM = os.getenv("OPSGENIE_FILTER_TEAM")

# Filter resources by users (comma-separated list of OpsGenie user IDs)
OPSGENIE_FILTER_USERS = [
    user_id.strip()
    for user_id in os.getenv("OPSGENIE_FILTER_USERS", "").split(",")
    if user_id.strip()
]

# Filter resources by name regex patterns
OPSGENIE_FILTER_SCHEDULE_REGEX = os.getenv("OPSGENIE_FILTER_SCHEDULE_REGEX")
OPSGENIE_FILTER_ESCALATION_POLICY_REGEX = os.getenv("OPSGENIE_FILTER_ESCALATION_POLICY_REGEX")
OPSGENIE_FILTER_INTEGRATION_REGEX = os.getenv("OPSGENIE_FILTER_INTEGRATION_REGEX")

# Whether to preserve existing notification rules when migrating users
PRESERVE_EXISTING_USER_NOTIFICATION_RULES = (
    os.getenv("PRESERVE_EXISTING_USER_NOTIFICATION_RULES", "true").lower() == "true"
)
