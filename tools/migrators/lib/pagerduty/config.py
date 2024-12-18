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
