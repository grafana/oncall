import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.grafana_plugin.helpers import GcomAPIClient
from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.grafana_plugin.helpers.gcom import get_active_instance_ids, get_deleted_instance_ids, get_stack_regions
from apps.user_management.models import Organization
from apps.user_management.models.region import sync_regions
from apps.user_management.sync import cleanup_organization, sync_organization, sync_team_members
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)

# celery beat will schedule start_sync_organizations for every 30 minutes
# to make sure that orgs are synced every 30 minutes, SYNC_PERIOD should be a little lower
SYNC_PERIOD = timezone.timedelta(minutes=25)
INACTIVE_PERIOD = timezone.timedelta(minutes=55)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def start_sync_organizations():
    sync_threshold = timezone.now() - SYNC_PERIOD

    organization_qs = Organization.objects.filter(last_time_synced__lte=sync_threshold)

    active_instance_ids, is_cloud_configured = get_active_instance_ids()
    if is_cloud_configured:
        if not active_instance_ids:
            logger.warning("Did not find any active instances!")
            return
        else:
            logger.debug(f"Found {len(active_instance_ids)} active instances")
            organization_qs = organization_qs.filter(stack_id__in=active_instance_ids)

    organization_pks = organization_qs.values_list("pk", flat=True)

    max_countdown = SYNC_PERIOD.seconds
    for idx, organization_pk in enumerate(organization_pks):
        countdown = idx % max_countdown  # Spread orgs evenly along SYNC_PERIOD
        sync_organization_async.apply_async((organization_pk,), countdown=countdown)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_organization_async(organization_pk):
    """
    This task is called periodically to sync an organization with Grafana.
    It runs syncronization without force_sync flag.
    """
    run_organization_sync(organization_pk, False)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), max_retries=1)
def plugin_sync_organization_async(organization_pk):
    """
    This task is called each time when the plugin is loaded.
    It runs syncronization with force_sync flag.
    Which means it will sync even if the organization was synced recently.
    """
    run_organization_sync(organization_pk, True)


def run_organization_sync(organization_pk, force_sync):
    logger.info(f"Start sync Organization {organization_pk}")

    try:
        organization = Organization.objects.get(pk=organization_pk)
    except Organization.DoesNotExist:
        logger.info(f"Organization {organization_pk} was not found")
        return

    if not force_sync:
        if organization.last_time_synced and timezone.now() - organization.last_time_synced < SYNC_PERIOD:
            logger.debug(f"Canceling sync for Organization {organization_pk}, since it was synced recently.")
            return
        if settings.GRAFANA_COM_API_TOKEN and settings.LICENSE == settings.CLOUD_LICENSE_NAME:
            client = GcomAPIClient(settings.GRAFANA_COM_API_TOKEN)
            instance_info = client.get_instance_info(organization.stack_id)
            if not instance_info or instance_info["status"] != client.STACK_STATUS_ACTIVE:
                logger.debug(f"Canceling sync for Organization {organization_pk}, as it is no longer active.")
                return

    sync_organization(organization)
    logger.info(f"Finish sync Organization {organization_pk}")


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), max_retries=1)
def start_cleanup_deleted_organizations():
    sync_threshold = timezone.now() - INACTIVE_PERIOD

    organization_qs = Organization.objects.filter(last_time_synced__lte=sync_threshold)

    deleted_instance_ids, is_cloud_configured = get_deleted_instance_ids()
    if is_cloud_configured:
        if not deleted_instance_ids:
            logger.warning("Did not find any deleted instances!")
            return
        else:
            logger.debug(f"Found {len(deleted_instance_ids)} deleted instances")
            organization_qs = organization_qs.filter(stack_id__in=deleted_instance_ids)

    organization_pks = organization_qs.values_list("pk", flat=True)

    logger.debug(f"Found {len(organization_pks)} deleted organizations not synced recently")
    max_countdown = INACTIVE_PERIOD.seconds
    for idx, organization_pk in enumerate(organization_pks):
        countdown = idx % max_countdown  # Spread orgs evenly
        cleanup_organization_async.apply_async((organization_pk,), countdown=countdown)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), max_retries=1)
def cleanup_organization_async(organization_pk):
    cleanup_organization(organization_pk)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), max_retries=1)
def start_sync_regions():
    regions, is_cloud_configured = get_stack_regions()
    if not is_cloud_configured:
        return

    if not regions:
        logger.warning("Did not find any stack-regions!")
        return

    sync_regions(regions)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), max_retries=1)
def sync_team_members_for_organization_async(organization_pk):
    try:
        organization = Organization.objects.get(pk=organization_pk)
    except Organization.DoesNotExist:
        logger.info(f"Organization {organization_pk} was not found")
        return

    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    sync_team_members(grafana_api_client, organization)
