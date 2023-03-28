import logging

import requests
from django.conf import settings

from .oncall_gateway_client import OnCallGatewayAPIClient
from .tasks import (
    create_oncall_connector_async,
    create_slack_connector_async_v2,
    delete_oncall_connector_async,
    delete_slack_connector_async_v2,
)

logger = logging.getLogger(__name__)


def create_oncall_connector(oncall_org_id: str, backend: str):
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.post_oncall_connector(oncall_org_id, backend)
    except Exception as e:
        logger.error(f"create_oncall_connector: failed " f"oncall_org_id={oncall_org_id} backend={backend} exc={e}")
        create_oncall_connector_async.apply_async((oncall_org_id, backend), countdown=2)


def delete_oncall_connector(oncall_org_id: str):
    delete_oncall_connector_async.delay(oncall_org_id)


def check_slack_installation_possible(oncall_org_id: str, slack_id: str, backend: str) -> bool:
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        response = client.check_slack_installation_possible(
            oncall_org_id=oncall_org_id, slack_id=slack_id, backend=backend
        )
        return response.status_code == 200
    except requests.exceptions.HTTPError as http_exc:
        logger.error(
            f"check_slack_installation_backend: slack installation impossible "
            f"oncall_org_id={oncall_org_id} slack_id={slack_id} backend={backend} exc={http_exc}"
        )

        return False


def create_slack_connector(oncall_org_id: str, slack_id: str, backend: str):
    client = OnCallGatewayAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.post_slack_connector(oncall_org_id, slack_id, backend)
    except Exception as e:
        logger.error(
            f"create_slack_connector: failed "
            f"oncall_org_id={oncall_org_id} slack_id={slack_id} backend={backend} exc={e}"
        )
        create_slack_connector_async_v2.apply_async(
            kwargs={"oncall_org_id": oncall_org_id, "slack_id": slack_id, "backend": backend}, countdown=2
        )


def delete_slack_connector(oncall_org_id: str):
    delete_slack_connector_async_v2.delay(oncall_org_id=oncall_org_id)
