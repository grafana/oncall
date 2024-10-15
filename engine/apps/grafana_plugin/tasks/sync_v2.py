import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.grafana_plugin.helpers.gcom import get_active_instance_ids
from apps.user_management.models import Organization
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def start_sync_organizations_v2():
    organization_qs = Organization.objects.all()
    active_instance_ids, is_cloud_configured = get_active_instance_ids()
    if is_cloud_configured:
        if not active_instance_ids:
            logger.warning("Did not find any active instances!")
            return
        else:
            logger.debug(f"Found {len(active_instance_ids)} active instances")
            organization_qs = organization_qs.filter(stack_id__in=active_instance_ids)

    logger.info(f"Found {len(organization_qs)} active organizations")
    batch = []
    batch_index = 0
    task_countdown_seconds = 0
    for org in organization_qs:
        if GrafanaAPIClient.validate_grafana_token_format(org.api_token):
            batch.append(org.pk)
            if len(batch) == settings.SYNC_V2_BATCH_SIZE:
                sync_organizations_v2.apply_async((batch,), countdown=task_countdown_seconds)
                batch = []
                batch_index += 1
                if batch_index == settings.SYNC_V2_MAX_TASKS:
                    batch_index = 0
                    task_countdown_seconds += settings.SYNC_V2_PERIOD_SECONDS
        else:
            logger.info(f"Skipping stack_slug={org.stack_slug}, api_token format is invalid or not set")
    if batch:
        sync_organizations_v2.apply_async((batch,), countdown=task_countdown_seconds)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def sync_organizations_v2(org_ids=None):
    organization_qs = Organization.objects.filter(id__in=org_ids)
    for org in organization_qs:
        client = GrafanaAPIClient(api_url=org.grafana_url, api_token=org.api_token)
        _, status = client.sync(org)
        if status["status_code"] != 200:
            logger.error(
                f"Failed to request sync org_id={org.pk} stack_slug={org.stack_slug} status_code={status['status_code']} url={status['url']} message={status['message']}"
            )
