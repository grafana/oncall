import datetime
import typing

from django.conf import settings


class AlertGroupsTotalMetricsDict(typing.TypedDict):
    integration_name: str
    team_name: str
    team_id: int
    org_id: int
    slug: str
    id: int
    firing: int
    acknowledged: int
    silenced: int
    resolved: int


class AlertGroupsResponseTimeMetricsDict(typing.TypedDict):
    integration_name: str
    team_name: str
    team_id: int
    org_id: int
    slug: str
    id: int
    response_time: list


class UserWasNotifiedOfAlertGroupsMetricsDict(typing.TypedDict):
    user_username: str
    org_id: int
    slug: str
    id: int
    counter: int


class RecalculateMetricsTimer(typing.TypedDict):
    recalculate_timeout: int
    forced_started: bool


class RecalculateOrgMetricsDict(typing.TypedDict):
    organization_id: int
    force: bool


METRICS_PREFIX = "oncall_" if settings.IS_OPEN_SOURCE else "grafanacloud_oncall_instance_"
USER_WAS_NOTIFIED_OF_ALERT_GROUPS = METRICS_PREFIX + "user_was_notified_of_alert_groups"

ALERT_GROUPS_TOTAL = "oncall_alert_groups_total"
ALERT_GROUPS_RESPONSE_TIME = "oncall_alert_groups_response_time_seconds"

METRICS_RESPONSE_TIME_CALCULATION_PERIOD = datetime.timedelta(days=7)

METRICS_CACHE_LIFETIME = 93600  # 26 hours. Should be higher than METRICS_RECALCULATE_CACHE_TIMEOUT

METRICS_CACHE_TIMER = "metrics_cache_timer"
METRICS_RECALCULATION_CACHE_TIMEOUT = 86400  # 24 hours. Should be less than METRICS_CACHE_LIFETIME
METRICS_RECALCULATION_CACHE_TIMEOUT_DISPERSE = (0, 3600)  # 1 hour

METRICS_ORGANIZATIONS_IDS = "metrics_organizations_ids"
METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT = 3600  # 1 hour
