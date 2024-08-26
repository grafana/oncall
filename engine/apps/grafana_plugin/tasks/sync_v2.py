import logging
import math
from time import sleep

from celery.utils.log import get_task_logger
from django.utils import timezone

from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.grafana_plugin.helpers.gcom import get_active_instance_ids
from apps.user_management.models import Organization
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.utils import task_lock

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


SYNC_PERIOD = timezone.timedelta(minutes=4)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=0)
def sync_organizations_v2(org_ids=None):
    lock_id = "sync_organizations_v2"
    with task_lock(lock_id, "main") as acquired:
        if acquired:
            if org_ids:
                logger.debug(f"Starting with provided {len(org_ids)} org_ids")
                organization_qs = Organization.objects.filter(id__in=org_ids)
            else:
                logger.debug("Starting with all org ids")
                organization_qs = Organization.objects.all()
            active_instance_ids, is_cloud_configured = get_active_instance_ids()
            if is_cloud_configured:
                if not active_instance_ids:
                    logger.warning("Did not find any active instances!")
                    return
                else:
                    logger.debug(f"Found {len(active_instance_ids)} active instances")
                    organization_qs = organization_qs.filter(stack_id__in=active_instance_ids)

            orgs_per_second = math.ceil(len(organization_qs) / SYNC_PERIOD.seconds)
            logger.info(f"Syncing {len(organization_qs)} organizations @ {orgs_per_second} per 1s pause")
            for idx, org in enumerate(organization_qs):
                if GrafanaAPIClient.validate_grafana_token_format(org.api_token):
                    client = GrafanaAPIClient(api_url=org.grafana_url, api_token=org.api_token)
                    _, status = client.sync()
                    if status["status_code"] != 200:
                        logger.error(
                            f"Failed to request sync stack_slug={org.stack_slug} status_code={status['status_code']} url={status['url']} message={status['message']}"
                        )
                    if idx % orgs_per_second == 0:
                        logger.info(f"Sleep 1s after {idx + 1} organizations processed")
                        sleep(1)
                else:
                    logger.info(f"Skipping stack_slug={org.stack_slug}, api_token format is invalid or not set")
        else:
            logger.info(f"Issuing sync requests already in progress lock_id={lock_id}, check slow outgoing requests")
