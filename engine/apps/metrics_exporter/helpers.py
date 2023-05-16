import random
import typing

from django.apps import apps
from django.core.cache import cache
from django.utils import timezone

from apps.alerts.constants import STATE_ACKNOWLEDGED, STATE_FIRING, STATE_RESOLVED, STATE_SILENCED
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
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
)


def get_organization_ids():
    """Try getting organizations ids from cache, otherwise get from db and save values in cache"""
    Organization = apps.get_model("user_management", "Organization")
    organizations_ids = cache.get(METRICS_ORGANIZATIONS_IDS, [])
    if not organizations_ids:
        organizations_ids = Organization.objects.all().values_list("id", flat=True)
        organizations_ids = list(organizations_ids)
        cache.set(organizations_ids, METRICS_ORGANIZATIONS_IDS, METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT)
    return organizations_ids


def get_organization_id_by_integration_id(integration_id):
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    integration = AlertReceiveChannel.objects.get(id=integration_id)
    return integration.organization_id


def get_response_time_period():
    """Returns period for response time calculation"""
    return timezone.now() - METRICS_RESPONSE_TIME_CALCULATION_PERIOD


def get_metrics_recalculation_timeout():
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


def get_metrics_cache_timer_key(organization_id):
    return f"{METRICS_CACHE_TIMER}_{organization_id}"


def get_metrics_cache_timer_for_organization(organization_id):
    key = get_metrics_cache_timer_key(organization_id)
    return cache.get(key)


def get_metric_alert_groups_total_key(organization_id):
    return f"{ALERT_GROUPS_TOTAL}_{organization_id}"


def get_metric_alert_groups_response_time_key(organization_id):
    return f"{ALERT_GROUPS_RESPONSE_TIME}_{organization_id}"


def metrics_update_integration_cache(integration):
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


def metrics_remove_deleted_integration_from_cache(integration):
    """Remove data related to deleted integration from metrics cache"""
    metrics_cache_timeout = get_metrics_cache_timeout(integration.organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(integration.organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(integration.organization_id)

    for metric_key in [metric_alert_groups_total_key, metric_alert_groups_response_time_key]:
        metric_cache = cache.get(metric_key)
        if metric_cache:
            metric_cache.pop(integration.id, None)
            cache.set(metric_key, metric_cache, timeout=metrics_cache_timeout)


def metrics_add_integration_to_cache(integration):
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
            "instance_slug": instance_slug,
            "instance_id": instance_id,
            "id": integration.organization_id,
            STATE_FIRING: 0,
            STATE_ACKNOWLEDGED: 0,
            STATE_RESOLVED: 0,
            STATE_SILENCED: 0,
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
            "instance_slug": instance_slug,
            "instance_id": instance_id,
            "id": integration.organization_id,
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
