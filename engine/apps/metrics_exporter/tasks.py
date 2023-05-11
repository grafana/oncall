import typing

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.alerts.constants import STATE_ACKNOWLEDGED, STATE_FIRING, STATE_RESOLVED, STATE_SILENCED
from apps.metrics_exporter.constants import (
    METRICS_ORGANIZATIONS_IDS,
    METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateMetricsTimer,
    RecalculateOrgMetricsDict,
)
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metrics_cache_timeout,
    get_metrics_cache_timer_key,
    get_metrics_recalculation_timeout,
    get_organization_id_by_integration_id,
    get_response_time_period,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.database import get_random_readonly_database_key_if_present_otherwise_default


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def save_organizations_ids_in_cache():
    Organization = apps.get_model("user_management", "Organization")
    organizations_ids = Organization.objects.all().values_list("id", flat=True)
    organizations_ids = list(organizations_ids)
    cache.set(organizations_ids, METRICS_ORGANIZATIONS_IDS, METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def start_calculate_and_cache_metrics(metrics_to_recalculate: list[RecalculateOrgMetricsDict]):
    """Start calculation metrics for each object in metrics_to_recalculate"""
    for counter, recalculation_data in enumerate(metrics_to_recalculate):
        # start immediately if recalculation starting has been forced
        countdown = 0 if recalculation_data.get("force") else counter
        calculate_and_cache_metrics.apply_async(kwargs=recalculation_data, countdown=countdown)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def calculate_and_cache_metrics(organization_id, force=False):
    """
    Calculate metrics for organization.
    Before calculation checks if calculation has already been started to avoid too frequent launch or parallel launch
    """
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    ONE_HOUR = 3600
    TWO_HOURS = 7200

    recalculate_timeout = get_metrics_recalculation_timeout()

    # check if recalculation has been already started
    metrics_cache_timer_key = get_metrics_cache_timer_key(organization_id)
    metrics_cache_timer = cache.get(metrics_cache_timer_key)
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
    cache.set(metrics_cache_timer_key, metrics_cache_timer, timeout=recalculate_timeout)

    integrations = (
        AlertReceiveChannel.objects.using(get_random_readonly_database_key_if_present_otherwise_default())
        .filter(~Q(integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE) & Q(organization__deleted_at__isnull=True))
        .select_related("organization", "team")
        .prefetch_related("alert_groups")
    )

    response_time_period = get_response_time_period()

    metric_alert_group_total: typing.Dict[int, AlertGroupsTotalMetricsDict] = {}
    metric_alert_group_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = {}

    states = {
        STATE_FIRING: AlertGroup.get_new_state_filter(),
        STATE_SILENCED: AlertGroup.get_silenced_state_filter(),
        STATE_ACKNOWLEDGED: AlertGroup.get_acknowledged_state_filter(),
        STATE_RESOLVED: AlertGroup.get_resolved_state_filter(),
    }

    for integration in integrations:
        instance_slug = integration.organization.stack_slug
        instance_id = integration.organization.stack_id
        # calculate states
        for state, alert_group_filter in states.items():
            metric_alert_group_total.setdefault(
                integration.id,
                {
                    "integration_name": integration.emojized_verbal_name,
                    "team_name": integration.team_name,
                    "team_id": integration.team_id_or_no_team,
                    "org_id": integration.organization.org_id,
                    "instance_slug": instance_slug,
                    "instance_id": instance_id,
                    "id": integration.organization_id,
                },
            )[state] = integration.alert_groups.filter(alert_group_filter).count()

        # calculate response time
        all_response_time = []
        alert_groups = integration.alert_groups.filter(started_at__gte=response_time_period)
        for alert_group in alert_groups:
            if alert_group.response_time:
                all_response_time.append(int(alert_group.response_time.total_seconds()))
            elif alert_group.state != STATE_FIRING:
                response_time = alert_group.get_response_time()
                if response_time:
                    alert_group.response_time = response_time
                    all_response_time.append(int(response_time.total_seconds()))

        metric_alert_group_response_time[integration.id] = {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "org_id": integration.organization.org_id,
            "instance_slug": instance_slug,
            "instance_id": instance_id,
            "id": integration.organization_id,
            "response_time": all_response_time,
        }

    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)

    metrics_cache_timeout = recalculate_timeout + TWO_HOURS
    cache.set(metric_alert_groups_total_key, metric_alert_group_total, timeout=metrics_cache_timeout)
    cache.set(metric_alert_groups_response_time_key, metric_alert_group_response_time, timeout=metrics_cache_timeout)
    if metrics_cache_timer["forced_started"]:
        metrics_cache_timer["forced_started"] = False
        cache.set(metrics_cache_timer_key, metrics_cache_timer, timeout=recalculate_timeout - ONE_HOUR)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def metrics_update_alert_groups_state_cache(states_diff, organization_id=None):
    """Update alert groups state metric cache for each integration in states_diff dict."""
    if not states_diff:
        return
    if not organization_id:
        integration_id = list(states_diff.keys())[0]
        organization_id = get_organization_id_by_integration_id(integration_id)

    metrics_cache_timeout = get_metrics_cache_timeout(organization_id)
    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
    metric_alert_groups_total = cache.get(metric_alert_groups_total_key, {})
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


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def metrics_update_alert_groups_response_time_cache(integrations_response_time, organization_id=None):
    """Update alert groups response time metric cache for each integration in `integrations_response_time` dict."""
    if not integrations_response_time:
        return
    if not organization_id:
        integration_id = list(integrations_response_time.keys())[0]
        organization_id = get_organization_id_by_integration_id(integration_id)

    metrics_cache_timeout = get_metrics_cache_timeout(organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)
    metric_alert_groups_response_time = cache.get(metric_alert_groups_response_time_key, {})
    for integration_id, integration_response_time in integrations_response_time.items():
        integration_response_time_metrics = metric_alert_groups_response_time.get(int(integration_id))
        if not integration_response_time_metrics:
            continue
        integration_response_time_metrics["response_time"].extend(integration_response_time)
    cache.set(metric_alert_groups_response_time_key, metric_alert_groups_response_time, timeout=metrics_cache_timeout)
