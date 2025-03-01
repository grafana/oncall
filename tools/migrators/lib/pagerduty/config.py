import os

from lib.base_config import *  # noqa: F401,F403

PAGERDUTY_API_TOKEN = os.environ["PAGERDUTY_API_TOKEN"]
PAGERDUTY_TO_ONCALL_CONTACT_METHOD_MAP = {
    "sms_contact_method": "notify_by_sms",
    "phone_contact_method": "notify_by_phone_call",
    "email_contact_method": "notify_by_email",
    "push_notification_contact_method": "notify_by_mobile_app",
}
PAGERDUTY_TO_ONCALL_VENDOR_MAP = {
    "Datadog": "datadog",
    "Pingdom": "pingdom",
    "Prometheus": "alertmanager",
    "PRTG": "prtg",
    "Stackdriver": "stackdriver",
    "UptimeRobot": "uptimerobot",
    "New Relic": "newrelic",
    "Zabbix Webhook (for 5.0 and 5.2)": "zabbix",
    "Elastic Alerts": "elastalert",
    "Firebase": "fabric",
    "Amazon CloudWatch": "amazon_sns",
}

# Experimental feature to migrate PD rulesets to OnCall integrations
EXPERIMENTAL_MIGRATE_EVENT_RULES = (
    os.getenv("EXPERIMENTAL_MIGRATE_EVENT_RULES", "false").lower() == "true"
)
# Set to true to include service & integration names in the ruleset name
EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES = (
    os.getenv("EXPERIMENTAL_MIGRATE_EVENT_RULES_LONG_NAMES", "false").lower() == "true"
)

# Set to true to migrate unsupported integrations to OnCall webhook integration
# https://grafana.com/docs/oncall/latest/integrations/available-integrations/configure-webhook/
UNSUPPORTED_INTEGRATION_TO_WEBHOOKS = (
    os.getenv("UNSUPPORTED_INTEGRATION_TO_WEBHOOKS", "false").lower() == "true"
)

MIGRATE_USERS = os.getenv("MIGRATE_USERS", "true").lower() == "true"

# Filter resources by team
PAGERDUTY_FILTER_TEAM = os.getenv("PAGERDUTY_FILTER_TEAM")

# Filter resources by users (comma-separated list of PagerDuty user IDs)
PAGERDUTY_FILTER_USERS = [
    user_id.strip()
    for user_id in os.getenv("PAGERDUTY_FILTER_USERS", "").split(",")
    if user_id.strip()
]

# Filter resources by name regex patterns
PAGERDUTY_FILTER_SCHEDULE_REGEX = os.getenv("PAGERDUTY_FILTER_SCHEDULE_REGEX")
PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX = os.getenv(
    "PAGERDUTY_FILTER_ESCALATION_POLICY_REGEX"
)
PAGERDUTY_FILTER_INTEGRATION_REGEX = os.getenv("PAGERDUTY_FILTER_INTEGRATION_REGEX")

# Whether to preserve existing notification rules when migrating users
PRESERVE_EXISTING_USER_NOTIFICATION_RULES = (
    os.getenv("PRESERVE_EXISTING_USER_NOTIFICATION_RULES", "true").lower() == "true"
)

# Environment variable to control verbose logging
VERBOSE_LOGGING = os.getenv("PAGERDUTY_VERBOSE_LOGGING", "false").lower() == "true"
