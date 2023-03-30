import typing

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from apps.alerts.constants import STATE_ACKNOWLEDGED, STATE_NEW, STATE_RESOLVED, STATE_SILENCED
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    METRICS_CACHE_TIMER,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateMetricsTimer,
)
from apps.metrics_exporter.helpers import get_metrics_recalculate_timeout, get_response_time_period
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def calculate_and_cache_metrics(force=False):  # todo:metrics org
    """todo:metrics: description"""

    recalculate_timeout = get_metrics_recalculate_timeout()

    # check recalculation metric timer to avoid parallel or too frequent launch
    metrics_cache_timer = cache.get(METRICS_CACHE_TIMER)
    if metrics_cache_timer:
        if not force or metrics_cache_timer.get("forced_started", False):
            return
        else:
            metrics_cache_timer["forced_started"] = True
    else:
        metrics_cache_timer: RecalculateMetricsTimer = {
            "recalculate_timeout": recalculate_timeout,
            "forced_started": force,
        }

    metrics_cache_timer["recalculate_timeout"] = recalculate_timeout
    cache.set(METRICS_CACHE_TIMER, metrics_cache_timer, timeout=recalculate_timeout)  # todo:metrics org

    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

    integrations = AlertReceiveChannel.objects.filter(~Q(integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE))
    response_time_period = get_response_time_period(timezone.now())

    metric_alert_group_total: typing.Dict[int, AlertGroupsTotalMetricsDict] = {}
    metric_alert_group_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = {}

    states = {
        STATE_NEW: AlertGroup.get_new_state_filter(),
        STATE_SILENCED: AlertGroup.get_silenced_state_filter(),
        STATE_ACKNOWLEDGED: AlertGroup.get_acknowledged_state_filter(),
        STATE_RESOLVED: AlertGroup.get_resolved_state_filter(),
    }

    alert_groups_to_update = []
    for integration in integrations:
        # calculate states
        for state, alert_group_filter in states.items():
            metric_alert_group_total.setdefault(
                integration.id,
                {
                    "integration_name": integration.emojized_verbal_name,
                    "team_name": integration.team_name,
                    "team_id": integration.team_id_or_no_team,
                },
            )[state] = integration.alert_groups.filter(alert_group_filter).count()

        # calculate response time
        all_response_time = []
        alert_groups = integration.alert_groups.filter(started_at__gte=response_time_period)
        for alert_group in alert_groups:
            if alert_group.response_time:
                all_response_time.append(int(alert_group.response_time.total_seconds()))
            elif alert_group.state != STATE_NEW:
                response_time = alert_group.get_response_time()
                if response_time:
                    alert_group.response_time = response_time
                    all_response_time.append(int(response_time.total_seconds()))
                    alert_groups_to_update.append(alert_group)

        metric_alert_group_response_time[integration.id] = {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "response_time": all_response_time,
        }

    cache.set(ALERT_GROUPS_TOTAL, metric_alert_group_total, timeout=recalculate_timeout)
    cache.set(ALERT_GROUPS_RESPONSE_TIME, metric_alert_group_response_time, timeout=recalculate_timeout)

    if metrics_cache_timer["forced_started"]:
        metrics_cache_timer["forced_started"] = False
        cache.set(METRICS_CACHE_TIMER, metrics_cache_timer, timeout=recalculate_timeout)  # todo:metrics org

    AlertGroup.all_objects.bulk_update(alert_groups_to_update, ["response_time"], batch_size=1000)
