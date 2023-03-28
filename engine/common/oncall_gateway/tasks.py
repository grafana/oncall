import requests
from celery.utils.log import get_task_logger
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .oncall_gateway_client import OnCallGatewayAPIClient

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def create_oncall_connector_async(oncall_org_id, backend):
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.post_oncall_connector(oncall_org_id, backend)
    except requests.exceptions.HTTPError as http_exc:
        if http_exc.response.status_code == 409:
            # 409 Indicates that it's impossible to create such connector.
            # More likely because it already exists.
            task_logger.error(
                f"Failed to create OnCallConnector oncall_org_id={oncall_org_id} backend={backend} exc={http_exc}"
            )
        else:
            raise http_exc
    except Exception as e:
        task_logger.error(f"Failed to create OnCallConnector oncall_org_id={oncall_org_id} backend={backend} exc={e}")
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def delete_oncall_connector_async(oncall_org_id):
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.delete_slack_connector(oncall_org_id)
    except requests.exceptions.HTTPError as http_exc:
        if http_exc.response.status_code == 404:
            # 404 indicates that connector was deleted already
            return
        else:
            task_logger.error(f"Failed to delete OnCallConnector oncall_org_id={oncall_org_id} exc={http_exc}")
            raise http_exc
    except Exception as e:
        task_logger.error(f"Failed to delete OnCallConnector oncall_org_id={oncall_org_id} exc={e}")
        raise e


# deprecated
@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=None,
)
def create_slack_connector_async(slack_id, backend):
    pass


# deprecated
@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=None,
)
def delete_slack_connector_async(slack_id):
    pass


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def create_slack_connector_async_v2(**kwargs):
    oncall_org_id = kwargs.get("oncall_org_id")
    slack_team_id = kwargs.get("slack_team_id")
    backend = kwargs.get("backend")
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.post_slack_connector(oncall_org_id, slack_team_id, backend)
    except requests.exceptions.HTTPError as http_exc:
        if http_exc.response.status_code == 409:
            # 409 Indicates that it's impossible to create such connector.
            # More likely because it already exists.
            task_logger.error(
                f"Failed to create SlackConnector oncall_org_id={oncall_org_id} backend={backend} exc={http_exc}"
            )
        else:
            raise http_exc
    except Exception as e:
        task_logger.error(f"Failed to create SlackConnector slack_id={oncall_org_id} backend={backend} exc={e}")
        raise e


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=100,
)
def delete_slack_connector_async_v2(**kwargs):
    oncall_org_id = kwargs.get("oncall_org_id")
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.delete_slack_connector(oncall_org_id)
    except requests.exceptions.HTTPError as http_exc:
        if http_exc.response.status_code == 404:
            # 404 indicates that connector was deleted already
            return
        else:
            raise http_exc
    except Exception as e:
        task_logger.error(f"Failed to delete SlackConnectorV2 oncall_org_id={oncall_org_id} exc={e}")
        raise e
