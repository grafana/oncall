import os
from urllib.parse import urljoin

PAGERDUTY = "pagerduty"
SPLUNK = "splunk"
OPSGENIE = "opsgenie"
MIGRATING_FROM = os.getenv("MIGRATING_FROM")
assert MIGRATING_FROM in (PAGERDUTY, SPLUNK, OPSGENIE)

MODE_PLAN = "plan"
MODE_MIGRATE = "migrate"
MODE = os.getenv("MODE", default=MODE_PLAN)
assert MODE in (MODE_PLAN, MODE_MIGRATE)

ONCALL_API_TOKEN = os.environ["ONCALL_API_TOKEN"]
ONCALL_API_URL = urljoin(
    os.environ["ONCALL_API_URL"].removesuffix("/") + "/",
    "api/v1/",
)
ONCALL_DELAY_OPTIONS = [1, 5, 15, 30, 60]

SCHEDULE_MIGRATION_MODE_ICAL = "ical"
SCHEDULE_MIGRATION_MODE_WEB = "web"
SCHEDULE_MIGRATION_MODE = os.getenv(
    "SCHEDULE_MIGRATION_MODE", SCHEDULE_MIGRATION_MODE_ICAL
)

# GRAFANA_SERVICE_ACCOUNT_URL is the URL format of a service account with
# Admin permission of the form: https://<namespace>:<token>@<server>
GRAFANA_SERVICE_ACCOUNT_URL = os.getenv("GRAFANA_SERVICE_ACCOUNT_URL", "")
