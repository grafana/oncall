import datetime
import random
import typing

from django.core.cache import cache
from django.utils import timezone

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    ALERT_GROUPS_RESPONSE_TIME,
    ALERT_GROUPS_TOTAL,
    METRICS_CACHE_LIFETIME,
    METRICS_CACHE_TIMER,
    METRICS_ORGANIZATIONS_IDS,
    METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT,
    METRICS_RECALCULATION_CACHE_TIMEOUT,
    METRICS_RECALCULATION_CACHE_TIMEOUT_DISPERSE,
    METRICS_RESPONSE_TIME_CALCULATION_PERIOD,
    USER_WAS_NOTIFIED_OF_ALERT_GROUPS,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateMetricsTimer,
    UserWasNotifiedOfAlertGroupsMetricsDict,
)

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertReceiveChannel


def get_organization_ids_from_db():
    from apps.alerts.models import AlertReceiveChannel

    # get only not deleted organizations that have integrations
    organizations_ids = (
        AlertReceiveChannel.objects.filter(organization__deleted_at__isnull=True)
        .values_list("organization_id", flat=True)
        .distinct()
    )
    organizations_ids = list(organizations_ids)
    return organizations_ids


def get_organization_ids():
    """Try to get organizations ids from cache, otherwise get from db and save values in cache"""
    organizations_ids = cache.get(METRICS_ORGANIZATIONS_IDS, [])
    if not organizations_ids:
        organizations_ids = get_organization_ids_from_db()
        cache.set(organizations_ids, METRICS_ORGANIZATIONS_IDS, METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT)
    return organizations_ids


def is_allowed_to_start_metrics_calculation(organization_id, force=False) -> bool:
    """Check if metrics_cache_timer doesn't exist or if recalculation was started by force."""
    recalculate_timeout = get_metrics_recalculation_timeout()
    metrics_cache_timer_key = get_metrics_cache_timer_key(organization_id)

    metrics_cache_timer: RecalculateMetricsTimer = cache.get(
        metrics_cache_timer_key,
        {
            "recalculate_timeout": recalculate_timeout,
            "forced_started": force,
        },
    )

    if not force or metrics_cache_timer.get("forced_started", False):
        return False
    else:
        metrics_cache_timer["forced_started"] = True

    metrics_cache_timer["recalculate_timeout"] = recalculate_timeout
    cache.set(metrics_cache_timer_key, metrics_cache_timer, timeout=recalculate_timeout)
    return True


def get_response_time_period() -> datetime.datetime:
    """Returns period for response time calculation"""
    return timezone.now() - METRICS_RESPONSE_TIME_CALCULATION_PERIOD


def get_metrics_recalculation_timeout() -> int:
    """
    Returns timeout when metrics should be recalculated.
    Add some dispersion to avoid starting recalculation tasks for all organizations at the same time.
    """
    return METRICS_RECALCULATION_CACHE_TIMEOUT + random.randint(*METRICS_RECALCULATION_CACHE_TIMEOUT_DISPERSE)


def get_metrics_cache_timeout(organization_id):
    metrics_cache_timer_key = get_metrics_cache_timer_key(organization_id)
    metrics_cache_timer = cache.get(metrics_cache_timer_key)
    if metrics_cache_timer:
        TWO_HOURS = 7200
        metrics_cache_timeout = int(metrics_cache_timer.get("recalculate_timeout")) + TWO_HOURS
    else:
        metrics_cache_timeout = METRICS_CACHE_LIFETIME
    return metrics_cache_timeout


def get_metrics_cache_timer_key(organization_id) -> str:
    return f"{METRICS_CACHE_TIMER}_{organization_id}"


def get_metrics_cache_timer_for_organization(organization_id):
    key = get_metrics_cache_timer_key(organization_id)
    return cache.get(key)


def get_metric_alert_groups_total_key(organization_id) -> str:
    return f"{ALERT_GROUPS_TOTAL}_{organization_id}"


def get_metric_alert_groups_response_time_key(organization_id) -> str:
    return f"{ALERT_GROUPS_RESPONSE_TIME}_{organization_id}"


def get_metric_user_was_notified_of_alert_groups_key(organization_id) -> str:
    return f"{USER_WAS_NOTIFIED_OF_ALERT_GROUPS}_{organization_id}"


def get_metric_calculation_started_key(metric_name) -> str:
    return f"calculation_started_for_{metric_name}"


def metrics_update_integration_cache(integration: "AlertReceiveChannel") -> None:
    """Update integration data in metrics cache"""
    metrics_cache_timeout = get_metrics_cache_timeout(integration.organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(integration.organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(integration.organization_id)

    for metric_key in [metric_alert_groups_total_key, metric_alert_groups_response_time_key]:
        metric_cache = cache.get(metric_key, {})
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
                cache.set(metric_key, metric_cache, timeout=metrics_cache_timeout)


def metrics_remove_deleted_integration_from_cache(integration: "AlertReceiveChannel"):
    """Remove data related to deleted integration from metrics cache"""
    metrics_cache_timeout = get_metrics_cache_timeout(integration.organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(integration.organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(integration.organization_id)

    for metric_key in [metric_alert_groups_total_key, metric_alert_groups_response_time_key]:
        metric_cache = cache.get(metric_key)
        if metric_cache:
            metric_cache.pop(integration.id, None)
            cache.set(metric_key, metric_cache, timeout=metrics_cache_timeout)


def metrics_add_integration_to_cache(integration: "AlertReceiveChannel"):
    """Add new integration data to metrics cache"""
    metrics_cache_timeout = get_metrics_cache_timeout(integration.organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(integration.organization_id)

    instance_slug = integration.organization.stack_slug
    instance_id = integration.organization.stack_id
    grafana_org_id = integration.organization.org_id
    metric_alert_groups_total: typing.Dict[int, AlertGroupsTotalMetricsDict] = cache.get(
        metric_alert_groups_total_key, {}
    )
    metric_alert_groups_total.setdefault(
        integration.id,
        {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "org_id": grafana_org_id,
            "slug": instance_slug,
            "id": instance_id,
            AlertGroupState.FIRING.value: 0,
            AlertGroupState.ACKNOWLEDGED.value: 0,
            AlertGroupState.RESOLVED.value: 0,
            AlertGroupState.SILENCED.value: 0,
        },
    )
    cache.set(metric_alert_groups_total_key, metric_alert_groups_total, timeout=metrics_cache_timeout)

    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(integration.organization_id)
    metric_alert_groups_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = cache.get(
        metric_alert_groups_response_time_key, {}
    )
    metric_alert_groups_response_time.setdefault(
        integration.id,
        {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "org_id": grafana_org_id,
            "slug": instance_slug,
            "id": instance_id,
            "response_time": [],
        },
    )
    cache.set(metric_alert_groups_response_time_key, metric_alert_groups_response_time, timeout=metrics_cache_timeout)


def metrics_bulk_update_team_label_cache(teams_updated_data, organization_id):
    """Update team related data in metrics cache for each team in `teams_updated_data`"""
    if not teams_updated_data:
        return
    metrics_cache_timeout = get_metrics_cache_timeout(organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)

    metric_alert_groups_total = cache.get(metric_alert_groups_total_key, {})
    metric_alert_groups_response_time = cache.get(metric_alert_groups_response_time_key, {})
    for team_id, team_data in teams_updated_data.items():
        for integration_id in metric_alert_groups_total:
            if metric_alert_groups_total[integration_id]["team_id"] == team_id:
                integration_response_time_metrics = metric_alert_groups_response_time.get(integration_id)
                if team_data["deleted"]:
                    metric_alert_groups_total[integration_id]["team_id"] = "no_team"
                    metric_alert_groups_total[integration_id]["team_name"] = "No team"
                    if integration_response_time_metrics:
                        integration_response_time_metrics["team_id"] = "no_team"
                        integration_response_time_metrics["team_name"] = "No team"
                else:
                    metric_alert_groups_total[integration_id]["team_name"] = team_data["team_name"]
                    if integration_response_time_metrics:
                        integration_response_time_metrics["team_name"] = team_data["team_name"]

    cache.set(metric_alert_groups_total_key, metric_alert_groups_total, timeout=metrics_cache_timeout)
    cache.set(metric_alert_groups_response_time_key, metric_alert_groups_response_time, timeout=metrics_cache_timeout)


def metrics_update_alert_groups_state_cache(states_diff, organization_id):
    """Update alert groups state metric cache for each integration in states_diff dict."""
    if not states_diff:
        return

    metrics_cache_timeout = get_metrics_cache_timeout(organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
    metric_alert_groups_total = cache.get(metric_alert_groups_total_key, {})
    if not metric_alert_groups_total:
        return
    for integration_id, integration_states_diff in states_diff.items():
        integration_alert_groups = metric_alert_groups_total.get(int(integration_id))
        if not integration_alert_groups:
            continue
        for previous_state, counter in integration_states_diff["previous_states"].items():
            if integration_alert_groups[previous_state] - counter > 0:
                integration_alert_groups[previous_state] -= counter
            else:
                integration_alert_groups[previous_state] = 0
        for new_state, counter in integration_states_diff["new_states"].items():
            integration_alert_groups[new_state] += counter

    cache.set(metric_alert_groups_total_key, metric_alert_groups_total, timeout=metrics_cache_timeout)


def metrics_update_alert_groups_response_time_cache(integrations_response_time, organization_id):
    """Update alert groups response time metric cache for each integration in `integrations_response_time` dict."""
    if not integrations_response_time:
        return

    metrics_cache_timeout = get_metrics_cache_timeout(organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)
    metric_alert_groups_response_time = cache.get(metric_alert_groups_response_time_key, {})
    if not metric_alert_groups_response_time:
        return
    for integration_id, integration_response_time in integrations_response_time.items():
        integration_response_time_metrics = metric_alert_groups_response_time.get(int(integration_id))
        if not integration_response_time_metrics:
            continue
        integration_response_time_metrics["response_time"].extend(integration_response_time)
    cache.set(metric_alert_groups_response_time_key, metric_alert_groups_response_time, timeout=metrics_cache_timeout)


def metrics_update_user_cache(user):
    """Update "user_was_notified_of_alert_groups" metric cache."""
    metrics_cache_timeout = get_metrics_cache_timeout(user.organization_id)
    metric_user_was_notified_key = get_metric_user_was_notified_of_alert_groups_key(user.organization_id)
    metric_user_was_notified: typing.Dict[int, UserWasNotifiedOfAlertGroupsMetricsDict] = cache.get(
        metric_user_was_notified_key, {}
    )

    metric_user_was_notified.setdefault(
        user.id,
        {
            "user_username": user.username,
            "org_id": user.organization.org_id,
            "slug": user.organization.stack_slug,
            "id": user.organization.stack_id,
            "counter": 0,
        },
    )["counter"] += 1

    cache.set(metric_user_was_notified_key, metric_user_was_notified, timeout=metrics_cache_timeout)
