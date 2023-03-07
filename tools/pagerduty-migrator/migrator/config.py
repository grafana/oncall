import os
from urllib.parse import urljoin

MODE_PLAN = "plan"
MODE_MIGRATE = "migrate"
MODE = os.getenv("MODE", default=MODE_PLAN)
assert MODE in (MODE_PLAN, MODE_MIGRATE)

PAGERDUTY_API_TOKEN = os.environ["PAGERDUTY_API_TOKEN"]
ONCALL_API_TOKEN = os.environ["ONCALL_API_TOKEN"]
ONCALL_API_URL = urljoin(
    os.environ["ONCALL_API_URL"].removesuffix("/") + "/",
    "api/v1/",
)

ONCALL_DELAY_OPTIONS = [1, 5, 15, 30, 60]
ONCALL_DEFAULT_CONTACT_METHOD = "notify_by_" + os.getenv(
    "ONCALL_DEFAULT_CONTACT_METHOD", default="email"
)
PAGERDUTY_TO_ONCALL_CONTACT_METHOD_MAP = {
    "sms_contact_method": "notify_by_sms",
    "phone_contact_method": "notify_by_phone_call",
    "email_contact_method": "notify_by_email",
    "push_notification_contact_method": ONCALL_DEFAULT_CONTACT_METHOD,
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

SCHEDULE_MIGRATION_MODE_ICAL = "ical"
SCHEDULE_MIGRATION_MODE_WEB = "web"
SCHEDULE_MIGRATION_MODE = os.getenv(
    "SCHEDULE_MIGRATION_MODE", SCHEDULE_MIGRATION_MODE_ICAL
)
