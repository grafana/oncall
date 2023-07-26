import logging
import random

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache

from apps.alerts.models.alert_group_counter import ConcurrentUpdateError
from apps.alerts.tasks import resolve_alert_group_by_source_if_needed
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.custom_celery_tasks.create_alert_base_task import CreateAlertBaseTask

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_task(
    base=CreateAlertBaseTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=1 if settings.DEBUG else None,
)
def create_alertmanager_alerts(alert_receive_channel_pk, alert, is_demo=False, force_route_id=None):
    from apps.alerts.models import Alert, AlertReceiveChannel

    alert_receive_channel = AlertReceiveChannel.objects_with_deleted.get(pk=alert_receive_channel_pk)
    if (
        alert_receive_channel.deleted_at is not None
        or alert_receive_channel.integration == AlertReceiveChannel.INTEGRATION_MAINTENANCE
    ):
        logger.info("AlertReceiveChannel alert ignored if deleted/maintenance")
        return

    try:
        alert = Alert.create(
            title=None,
            message=None,
            image_url=None,
            link_to_upstream_details=None,
            alert_receive_channel=alert_receive_channel,
            integration_unique_data=None,
            raw_request_data=alert,
            enable_autoresolve=False,
            is_demo=is_demo,
            force_route_id=force_route_id,
        )
    except ConcurrentUpdateError:
        # This error is raised when there are concurrent updates on AlertGroupCounter due to optimistic lock on it.
        # The idea is to not block the worker with a database lock and retry the task in case of concurrent updates.
        countdown = random.randint(1, 10)
        create_alertmanager_alerts.apply_async((alert_receive_channel_pk, alert), countdown=countdown)
        logger.warning(f"Retrying the task gracefully in {countdown} seconds due to ConcurrentUpdateError")
        return

    if alert_receive_channel.allow_source_based_resolving:
        alert_group = alert.group
        if alert_group.resolved_by != alert_group.NOT_YET_STOP_AUTORESOLVE:
            task = resolve_alert_group_by_source_if_needed.apply_async((alert.group.pk,), countdown=5)
            alert.group.active_resolve_calculation_id = task.id
            alert.group.save(update_fields=["active_resolve_calculation_id"])

    logger.info(f"Created alert {alert.pk} for alert group {alert.group.pk}")


@shared_task(
    base=CreateAlertBaseTask,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=1 if settings.DEBUG else None,
)
def create_alert(
    title,
    message,
    image_url,
    link_to_upstream_details,
    alert_receive_channel_pk,
    integration_unique_data,
    raw_request_data,
    is_demo=False,
    force_route_id=None,
):
    from apps.alerts.models import Alert, AlertReceiveChannel

    try:
        alert_receive_channel = AlertReceiveChannel.objects.get(pk=alert_receive_channel_pk)
    except AlertReceiveChannel.DoesNotExist:
        return

    if image_url is not None:
        image_url = str(image_url)[:299]

    try:
        alert = Alert.create(
            title=title,
            message=message,
            image_url=image_url,
            link_to_upstream_details=link_to_upstream_details,
            alert_receive_channel=alert_receive_channel,
            integration_unique_data=integration_unique_data,
            raw_request_data=raw_request_data,
            force_route_id=force_route_id,
            is_demo=is_demo,
        )
        logger.info(f"Created alert {alert.pk} for alert group {alert.group.pk}")
    except ConcurrentUpdateError:
        # This error is raised when there are concurrent updates on AlertGroupCounter due to optimistic lock on it.
        # The idea is to not block the worker with a database lock and retry the task in case of concurrent updates.
        countdown = random.randint(1, 10)
        create_alert.apply_async(
            (
                title,
                message,
                image_url,
                link_to_upstream_details,
                alert_receive_channel_pk,
                integration_unique_data,
                raw_request_data,
            ),
            countdown=countdown,
        )
        logger.warning(f"Retrying the task gracefully in {countdown} seconds due to ConcurrentUpdateError")


@shared_dedicated_queue_retry_task()
def start_notify_about_integration_ratelimit(team_id, text, **kwargs):
    notify_about_integration_ratelimit_in_slack.apply_async(
        args=(
            team_id,
            text,
        ),
        kwargs=kwargs,
        expires=60 * 5,
    )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else 5
)
def notify_about_integration_ratelimit_in_slack(organization_id, text, **kwargs):
    # TODO: Review ratelimits
    from apps.user_management.models import Organization

    try:
        organization = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        logger.warning(f"Organization {organization_id} does not exist")
        return

    cache_key = f"notify_about_integration_ratelimit_in_slack_{organization.pk}"
    if cache.get(cache_key):
        logger.debug(f"Message was sent recently for organization {organization_id}")
        return
    else:
        cache.set(cache_key, True, 60 * 15)  # Set cache before sending message to make sure we don't ratelimit slack
        slack_team_identity = organization.slack_team_identity
        if slack_team_identity is not None:
            try:
                sc = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
                sc.api_call(
                    "chat.postMessage", channel=organization.general_log_channel_id, text=text, team=slack_team_identity
                )
            except SlackAPIException as e:
                logger.warning(f"Slack exception {e} while sending message for organization {organization_id}")
