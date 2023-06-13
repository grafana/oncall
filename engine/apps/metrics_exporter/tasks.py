import typing

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.alerts.constants import AlertGroupState
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
    get_metrics_cache_timer_key,
    get_metrics_recalculation_timeout,
    get_response_time_period,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.database import get_random_readonly_database_key_if_present_otherwise_default


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def save_organizations_ids_in_cache():
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    # save only organizations with integrations
    organizations_ids = AlertReceiveChannel.objects.all().values_list("organization_id", flat=True).distinct()
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
        .filter(
            ~Q(integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE)
            & Q(organization__deleted_at__isnull=True)
            & Q(organization_id=organization_id)
        )
        .select_related("organization", "team")
        .prefetch_related("alert_groups")
    )

    response_time_period = get_response_time_period()

    metric_alert_group_total: typing.Dict[int, AlertGroupsTotalMetricsDict] = {}
    metric_alert_group_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = {}

    states = {
        AlertGroupState.FIRING.value: AlertGroup.get_new_state_filter(),
        AlertGroupState.SILENCED.value: AlertGroup.get_silenced_state_filter(),
        AlertGroupState.ACKNOWLEDGED.value: AlertGroup.get_acknowledged_state_filter(),
        AlertGroupState.RESOLVED.value: AlertGroup.get_resolved_state_filter(),
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
                    "slug": instance_slug,
                    "id": instance_id,
                },
            )[state] = integration.alert_groups.filter(alert_group_filter).count()

        # calculate response time
        all_response_time = []
        alert_groups = integration.alert_groups.filter(started_at__gte=response_time_period)
        for alert_group in alert_groups:
            if alert_group.response_time:
                all_response_time.append(int(alert_group.response_time.total_seconds()))
            elif alert_group.state != AlertGroupState.FIRING:
                # get calculated value from current alert group information
                response_time = alert_group._get_response_time()
                if response_time:
                    all_response_time.append(int(response_time.total_seconds()))

        metric_alert_group_response_time[integration.id] = {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "org_id": integration.organization.org_id,
            "slug": instance_slug,
            "id": instance_id,
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
