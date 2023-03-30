import typing


class AlertGroupsTotalMetricsDict(typing.TypedDict):
    integration_name: str
    team_name: str
    team_id: int
    new: int
    acknowledged: int
    silenced: int
    resolved: int


class AlertGroupsResponseTimeMetricsDict(typing.TypedDict):
    integration_name: str
    team_name: str
    team_id: int
    response_time: list


ALERT_GROUPS_TOTAL = "oncall_alert_groups_total"
ALERT_GROUPS_RESPONSE_TIME = "oncall_alert_groups_response_time_7d_seconds"

METRICS_CACHE_TIMER = "metrics_cache_timer"
METRICS_RECALCULATE_CACHE_TIMEOUT = 86400  # 24 hours
METRICS_RECALCULATE_CACHE_TIMEOUT_DISPERSE = (0, 3600)  # 1 hour

METRICS_CACHE_LIFETIME = 86400  # todo:metrics
