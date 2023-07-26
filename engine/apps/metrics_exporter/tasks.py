import typing

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q

from apps.alerts.constants import AlertGroupState
from apps.metrics_exporter.constants import (
    METRICS_ORGANIZATIONS_IDS,
    METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT,
    AlertGroupsResponseTimeMetricsDict,
    AlertGroupsTotalMetricsDict,
    RecalculateOrgMetricsDict,
    UserWasNotifiedOfAlertGroupsMetricsDict,
)
from apps.metrics_exporter.helpers import (
    get_metric_alert_groups_response_time_key,
    get_metric_alert_groups_total_key,
    get_metric_calculation_started_key,
    get_metric_user_was_notified_of_alert_groups_key,
    get_metrics_cache_timer_key,
    get_metrics_recalculation_timeout,
    get_organization_ids,
    get_organization_ids_from_db,
    get_response_time_period,
    is_allowed_to_start_metrics_calculation,
)
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.database import get_random_readonly_database_key_if_present_otherwise_default


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def save_organizations_ids_in_cache():
    organizations_ids = get_organization_ids_from_db()
    cache.set(organizations_ids, METRICS_ORGANIZATIONS_IDS, METRICS_ORGANIZATIONS_IDS_CACHE_TIMEOUT)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def start_calculate_and_cache_metrics(metrics_to_recalculate: list[RecalculateOrgMetricsDict]):
    """Start calculation metrics for each object in metrics_to_recalculate"""
    for counter, recalculation_data in enumerate(metrics_to_recalculate):
        if not is_allowed_to_start_metrics_calculation(**recalculation_data):
            continue
        # start immediately if recalculation starting has been forced
        countdown = 0 if recalculation_data.get("force") else counter
        calculate_and_cache_metrics.apply_async(kwargs=recalculation_data, countdown=countdown)
        calculate_and_cache_user_was_notified_metric.apply_async(
            (recalculation_data["organization_id"],), countdown=countdown
        )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def start_recalculation_for_new_metric(metric_name):
    TEN_MINUTES = 600
    calculation_started_key = get_metric_calculation_started_key(metric_name)
    is_calculation_started = cache.get(calculation_started_key)
    if is_calculation_started:
        return
    cache.set(calculation_started_key, True, timeout=TEN_MINUTES)
    org_ids = set(get_organization_ids())
    countdown = 0
    for counter, organization_id in enumerate(org_ids):
        if counter % 10 == 0:
            countdown += 1
        calculate_and_cache_user_was_notified_metric.apply_async((organization_id,), countdown=countdown)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def calculate_and_cache_metrics(organization_id, force=False):
    """
    Calculate integrations metrics for organization.
    """
    from apps.alerts.models import AlertGroup, AlertReceiveChannel
    from apps.user_management.models import Organization

    ONE_HOUR = 3600
    TWO_HOURS = 7200

    organization = Organization.objects.filter(pk=organization_id).first()
    if not organization:
        return

    integrations = (
        AlertReceiveChannel.objects.using(get_random_readonly_database_key_if_present_otherwise_default())
        .filter(~Q(integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE) & Q(organization_id=organization_id))
        .select_related("team")
    )

    response_time_period = get_response_time_period()

    instance_slug = organization.stack_slug
    instance_id = organization.stack_id
    instance_org_id = organization.org_id

    metric_alert_group_total: typing.Dict[int, AlertGroupsTotalMetricsDict] = {}
    metric_alert_group_response_time: typing.Dict[int, AlertGroupsResponseTimeMetricsDict] = {}

    states = {
        AlertGroupState.FIRING.value: AlertGroup.get_new_state_filter(),
        AlertGroupState.SILENCED.value: AlertGroup.get_silenced_state_filter(),
        AlertGroupState.ACKNOWLEDGED.value: AlertGroup.get_acknowledged_state_filter(),
        AlertGroupState.RESOLVED.value: AlertGroup.get_resolved_state_filter(),
    }

    for integration in integrations:
        # calculate states
        for state, alert_group_filter in states.items():
            metric_alert_group_total.setdefault(
                integration.id,
                {
                    "integration_name": integration.emojized_verbal_name,
                    "team_name": integration.team_name,
                    "team_id": integration.team_id_or_no_team,
                    "org_id": instance_org_id,
                    "slug": instance_slug,
                    "id": instance_id,
                },
            )[state] = integration.alert_groups.filter(alert_group_filter).count()

        # get response time
        all_response_time = integration.alert_groups.filter(
            started_at__gte=response_time_period,
            response_time__isnull=False,
        ).values_list("response_time", flat=True)

        all_response_time_seconds = [int(response_time.total_seconds()) for response_time in all_response_time]

        metric_alert_group_response_time[integration.id] = {
            "integration_name": integration.emojized_verbal_name,
            "team_name": integration.team_name,
            "team_id": integration.team_id_or_no_team,
            "org_id": instance_org_id,
            "slug": instance_slug,
            "id": instance_id,
            "response_time": all_response_time_seconds,
        }

    metric_alert_groups_total_key = get_metric_alert_groups_total_key(organization_id)
    metric_alert_groups_response_time_key = get_metric_alert_groups_response_time_key(organization_id)

    recalculate_timeout = get_metrics_recalculation_timeout()
    metrics_cache_timeout = recalculate_timeout + TWO_HOURS
    cache.set(metric_alert_groups_total_key, metric_alert_group_total, timeout=metrics_cache_timeout)
    cache.set(metric_alert_groups_response_time_key, metric_alert_group_response_time, timeout=metrics_cache_timeout)
    if force:
        metrics_cache_timer_key = get_metrics_cache_timer_key(organization_id)
        metrics_cache_timer = cache.get(metrics_cache_timer_key)
        metrics_cache_timer["forced_started"] = False
        cache.set(metrics_cache_timer_key, metrics_cache_timer, timeout=recalculate_timeout - ONE_HOUR)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def calculate_and_cache_user_was_notified_metric(organization_id):
    """
    Calculate metric "user_was_notified_of_alert_groups" for organization.
    """
    from apps.base.models import UserNotificationPolicyLogRecord
    from apps.user_management.models import Organization

    TWO_HOURS = 7200

    organization = Organization.objects.filter(pk=organization_id).first()
    if not organization:
        return

    users = (
        User.objects.using(get_random_readonly_database_key_if_present_otherwise_default())
        .filter(organization_id=organization_id)
        .annotate(num_logs=Count("personal_log_records"))
        .filter(num_logs__gte=1)
    )

    instance_slug = organization.stack_slug
    instance_id = organization.stack_id
    instance_org_id = organization.org_id

    metric_user_was_notified: typing.Dict[int, UserWasNotifiedOfAlertGroupsMetricsDict] = {}

    for user in users:
        counter = (
            user.personal_log_records.filter(type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED)
            .values("alert_group")
            .distinct()
            .count()
        )

        if counter == 0:  # means that user has no successful notifications
            continue

        metric_user_was_notified[user.id] = {
            "user_username": user.username,
            "org_id": instance_org_id,
            "slug": instance_slug,
            "id": instance_id,
            "counter": counter,
        }

    metric_user_was_notified_key = get_metric_user_was_notified_of_alert_groups_key(organization_id)

    recalculate_timeout = get_metrics_recalculation_timeout()
    metrics_cache_timeout = recalculate_timeout + TWO_HOURS
    cache.set(metric_user_was_notified_key, metric_user_was_notified, timeout=metrics_cache_timeout)
