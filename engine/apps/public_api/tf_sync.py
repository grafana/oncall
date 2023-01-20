import logging

from django.core.cache import cache

from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.grafana_plugin.tasks import sync_team_members_for_organization_async
from apps.user_management.sync import sync_teams, sync_users

logger = logging.getLogger(__name__)

SYNC_REQUEST_TIMEOUT = 5
SYNC_PERIOD = 60


def is_request_from_terraform(request) -> bool:
    if "terraform-provider-grafana" in request.META.get("HTTP_USER_AGENT", ""):
        return True
    return False


def sync_users_on_tf_request(organization):
    v = cache.get(f"sync_users_on_tf_request_{organization.id}")
    print(f"CACHE_{v}")
    if not cache.get(f"sync_users_on_tf_request_{organization.id}"):
        logger.info(f"Start sync_users_on_tf_request organization_id={organization.id}")
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        cache.set(f"sync_users_on_tf_request_{organization.id}", True, SYNC_PERIOD)
        sync_users(client, organization, timeout=SYNC_REQUEST_TIMEOUT)


def sync_teams_on_tf_request(organization):
    if not cache.get(f"sync_teams_on_tf_request_{organization.id}"):
        logger.info(f"Start sync_teams_on_tf_request organization_id={organization.id}")
        cache.set(f"sync_teams_on_tf_request_{organization.id}", True, SYNC_PERIOD)
        client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        sync_teams(client, organization, timeout=SYNC_REQUEST_TIMEOUT)
        sync_team_members_for_organization_async.apply_async((organization.id,))
