import random

from django.core.cache import cache
from django.utils import timezone

from apps.alerts.constants import STATE_ACKNOWLEDGED, STATE_NEW, STATE_RESOLVED, STATE_SILENCED
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    METRICS_CACHE_LIFETIME,
    METRICS_CACHE_TIMER,
    METRICS_RECALCULATE_CACHE_TIMEOUT,
    METRICS_RECALCULATE_CACHE_TIMEOUT_DISPERSE,
)


def get_response_time_period(now):
    response_time_period = now - timezone.timedelta(days=7)
    return response_time_period


def get_metrics_recalculate_timeout():
    return METRICS_RECALCULATE_CACHE_TIMEOUT + random.randint(*METRICS_RECALCULATE_CACHE_TIMEOUT_DISPERSE)


def get_metrics_cache_timeout():  # todo:metrics org_id
    metrics_cache_timeout = cache.get(METRICS_CACHE_TIMER)
    metrics_cache_timeout = int(metrics_cache_timeout) if metrics_cache_timeout else METRICS_CACHE_LIFETIME
    return metrics_cache_timeout


def metrics_update_integration_cache(integration):  # todo:metrics org_id
    # todo:metrics: description
    metrics_cache_timeout = get_metrics_cache_timeout()
    for metric in [ALERT_GROUPS_TOTAL, ALERT_GROUPS_RESPONSE_TIME]:
        metric_cache = cache.get(metric, {})
        integration_metric_cache = metric_cache.get(integration.id)
        if integration_metric_cache:
            cache_updated = False
            if integration_metric_cache["team_id"] != integration.team_id_or_no_team:
                integration_metric_cache["team_id"] = integration.team_id_or_no_team
                integration_metric_cache["team_name"] = integration.team_name
                cache_updated = True
            if integration_metric_cache["integration_name"] != integration.emojized_verbal_name:
                integration_metric_cache["integration_name"] = integration.emojized_verbal_name
                cache_updated = True
            if cache_updated:
                cache.set(metric, metric_cache, timeout=metrics_cache_timeout)


def metrics_remove_deleted_integration_from_cache(integration):  # todo:metrics org_id
    # todo:metrics: description
    metrics_cache_timeout = get_metrics_cache_timeout()
    for metric in [ALERT_GROUPS_TOTAL, ALERT_GROUPS_RESPONSE_TIME]:
        metric_cache = cache.get(metric)
        metric_cache.pop(integration.id, None)
        cache.set(metric, metric_cache, timeout=metrics_cache_timeout)


def metrics_add_integration_to_cache(integration):  # todo:metrics org_id
    # todo:metrics: description
    metrics_cache_timeout = get_metrics_cache_timeout()
    alert_groups_total_metrics = cache.get(ALERT_GROUPS_TOTAL, {})
    alert_groups_total_metrics.setdefault(
        integration.id,
        {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            STATE_NEW: 0,
            STATE_ACKNOWLEDGED: 0,
            STATE_RESOLVED: 0,
            STATE_SILENCED: 0,
        },
    )
    cache.set(ALERT_GROUPS_TOTAL, alert_groups_total_metrics, timeout=metrics_cache_timeout)

    alert_groups_response_time_metrics = cache.get(ALERT_GROUPS_RESPONSE_TIME, {})
    alert_groups_response_time_metrics.setdefault(
        integration.id,
        {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "response_time": [],
        },
    )
    cache.set(ALERT_GROUPS_RESPONSE_TIME, alert_groups_response_time_metrics, timeout=metrics_cache_timeout)


def metrics_bulk_update_team_label_cache(teams_updated_data):  # todo:metrics org_id
    # todo:metrics: description
    if not teams_updated_data:
        return
    metrics_cache_timeout = get_metrics_cache_timeout()
    alert_groups_total_metrics = cache.get(ALERT_GROUPS_TOTAL, {})
    response_time_metrics = cache.get(ALERT_GROUPS_RESPONSE_TIME, {})
    for team_id, team_data in teams_updated_data.items():
        for integration_id in alert_groups_total_metrics:
            if alert_groups_total_metrics[integration_id]["team_id"] == team_id:
                integration_response_time_metrics = response_time_metrics.get(integration_id)
                if team_data["deleted"]:
                    alert_groups_total_metrics[integration_id]["team_id"] = None
                    alert_groups_total_metrics[integration_id]["team_name"] = "General"
                    if integration_response_time_metrics:
                        integration_response_time_metrics["team_id"] = None
                        integration_response_time_metrics["team_name"] = "General"
                else:
                    alert_groups_total_metrics[integration_id]["team_name"] = team_data["team_name"]
                    if integration_response_time_metrics:
                        integration_response_time_metrics["team_name"] = team_data["team_name"]

    cache.set(ALERT_GROUPS_TOTAL, alert_groups_total_metrics, timeout=metrics_cache_timeout)
    cache.set(ALERT_GROUPS_RESPONSE_TIME, response_time_metrics, timeout=metrics_cache_timeout)


def metrics_update_alert_groups_state_cache(states_diff):  # todo:metrics org_id
    # todo:metrics: description
    if not states_diff:
        return
    metrics_cache_timeout = get_metrics_cache_timeout()
    alert_groups_total_metrics = cache.get(ALERT_GROUPS_TOTAL, {})
    for integration_id, integration_states_diff in states_diff.items():
        integration_alert_groups = alert_groups_total_metrics.get(integration_id)
        if not integration_alert_groups:
            continue
        for previous_state, counter in integration_states_diff["previous_states"].items():
            if integration_alert_groups[previous_state] - counter > 0:
                integration_alert_groups[previous_state] -= counter
            else:
                integration_alert_groups[previous_state] = 0
        for new_state, counter in integration_states_diff["new_states"].items():
            integration_alert_groups[new_state] += counter
    cache.set(ALERT_GROUPS_TOTAL, alert_groups_total_metrics, timeout=metrics_cache_timeout)


def metrics_update_alert_groups_response_time_cache(integrations_response_time):  # todo:metrics org_id
    # todo:metrics: description
    if not integrations_response_time:
        return
    metrics_cache_timeout = get_metrics_cache_timeout()
    alert_groups_response_time_metrics = cache.get(ALERT_GROUPS_RESPONSE_TIME, {})
    for integration_id, integration_response_time in integrations_response_time.items():
        integration_response_time_metrics = alert_groups_response_time_metrics.get(integration_id)
        if not integration_response_time_metrics:
            continue
        integration_response_time_metrics["response_time"].extend(integration_response_time)
    cache.set(ALERT_GROUPS_RESPONSE_TIME, alert_groups_response_time_metrics, timeout=metrics_cache_timeout)
