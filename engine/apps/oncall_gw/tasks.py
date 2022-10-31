from celery.utils.log import get_task_logger
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .oncall_gw_client import OnCallGwAPIClient

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def create_oncall_connector_async(oncall_org_id, backend):
    client = OnCallGwAPIClient(settings.ONCALL_GW_URL, settings.ONCALL_GW_API_TOKEN)
    try:
        client.post_oncall_connector(oncall_org_id, backend)
    except Exception as e:
        task_logger.error(f"Failed to create OnCallConnector oncall_org_id={oncall_org_id} backend={backend} exc={e}")
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def create_slack_connector_async(slack_id, backend):
    client = OnCallGwAPIClient(settings.ONCALL_GW_URL, settings.ONCALL_GW_API_TOKEN)
    try:
        client.post_slack_connector(slack_id, backend)
    except Exception as e:
        task_logger.error(f"Failed to create OnCallConnector slack_id={slack_id} backend={backend} exc={e}")
        raise e
