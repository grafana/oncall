import logging

import requests
from django.conf import settings

from .oncall_gw_client import OnCallGwAPIClient
from .tasks import create_oncall_connector_async, create_slack_connector_async

logger = logging.getLogger(__name__)


def create_oncall_connector(oncall_org_id: str, backend: str):
    client = OnCallGwAPIClient(settings.ONCALL_GW_URL, settings.ONCALL_GW_API_TOKEN)
    try:
        client.post_oncall_connector(oncall_org_id, backend)
    except Exception as e:
        logger.error(f"Failed to create_oncall_connector oncall_org_id={oncall_org_id} backend={backend} exc={e}")
        create_oncall_connector_async.apply_async((oncall_org_id, backend), countdown=2)


def check_slack_installation_backend(slack_id: str, backend: str):
    client = OnCallGwAPIClient(settings.ONCALL_GW_URL, settings.ONCALL_GW_API_TOKEN)
    try:
        slack_connector, response = client.get_slack_connector(slack_id)
        if slack_connector.backend == backend:
            return True
        else:
            return False
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            return True


def create_slack_connector(slack_id: str, backend: str):
    client = OnCallGwAPIClient(settings.ONCALL_GW_URL, settings.ONCALL_GW_API_TOKEN)
    try:
        client.post_slack_connector(slack_id, backend)
    except Exception as e:
        logger.error(f"Failed to create_oncall_connector slack_id={slack_id} backend={backend} exc={e}")
        create_slack_connector_async.apply_async((slack_id, backend), countdown=2)
