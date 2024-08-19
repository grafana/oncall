"""
Set of utils to handle oncall and chatops-proxy interaction.
"""
import logging
import typing
from urllib.parse import urljoin

from django.conf import settings

from .client import APP_TYPE_ONCALL, PROVIDER_TYPE_SLACK, ChatopsProxyAPIClient, ChatopsProxyAPIException
from .register_oncall_tenant import register_oncall_tenant
from .tasks import (
    link_slack_team_async,
    register_oncall_tenant_async,
    unlink_slack_team_async,
    unregister_oncall_tenant_async,
)

logger = logging.getLogger(__name__)


def get_installation_link_from_chatops_proxy(user) -> typing.Optional[str]:
    """
    get_installation_link_from_chatops_proxy fetches slack installation link from chatops proxy.
    If there is no existing slack installation - if returns link, If slack already installed, it returns None.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    org = user.organization
    try:
        link, _ = client.get_slack_oauth_link(
            org.stack_id,
            user.user_id,
            urljoin(org.web_link, "settings?tab=ChatOps&chatOpsTab=Slack"),
            APP_TYPE_ONCALL,
        )
        return link
    except ChatopsProxyAPIException as api_exc:
        if api_exc.status == 409:
            return None
        logger.exception(
            "Error while getting installation link from chatops proxy: " "error=%s",
            api_exc,
        )
        raise api_exc


def get_slack_oauth_response_from_chatops_proxy(stack_id) -> dict:
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    slack_installation, _ = client.get_oauth_installation(stack_id, PROVIDER_TYPE_SLACK)
    return slack_installation.oauth_response


def register_oncall_tenant_with_async_fallback(org):
    """
    register_oncall_tenant tries to register oncall tenant synchronously and fall back to task in case of any exceptions
    to make sure that tenant is registered.
    First attempt is synchronous to register tenant ASAP to not miss any chatops requests.
    """
    try:
        register_oncall_tenant(org)
    except Exception as e:
        logger.error(f"create_oncall_connector: failed organization_id={org}  exc={e}")
        register_oncall_tenant_async.apply_async(
            kwargs={
                "service_tenant_id": str(org.uuid),
                "cluster_slug": settings.ONCALL_BACKEND_REGION,
                "service_type": APP_TYPE_ONCALL,
                "stack_id": org.stack_id,
                "stack_slug": org.stack_slug,
                "org_id": org.id,
            },
            countdown=2,
        )


def unregister_oncall_tenant(service_tenant_id: str, cluster_slug: str):
    """
    unregister_oncall_tenant unregisters tenant asynchronously.
    """
    unregister_oncall_tenant_async.apply_async(
        kwargs={
            "service_tenant_id": service_tenant_id,
            "cluster_slug": cluster_slug,
            "service_type": APP_TYPE_ONCALL,
        },
        countdown=2,
    )


def can_link_slack_team(
    service_tenant_id: str,
    slack_team_id: str,
    cluster_slug: str,
) -> bool:
    """
    can_link_slack_team checks if it's possible to link slack workspace to oncall tenant located in cluster.
    All oncall tenants linked to same slack team should have same cluster.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        response = client.can_slack_link(service_tenant_id, cluster_slug, slack_team_id, APP_TYPE_ONCALL)
        return response.status_code == 200
    except Exception as e:
        logger.error(
            f"can_link_slack_team: slack installation impossible: {e} "
            f"service_tenant_id={service_tenant_id} slack_team_id={slack_team_id} cluster_slug={cluster_slug}"
        )

        return False


def link_slack_team(service_tenant_id: str, slack_team_id: str):
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.link_slack_team(service_tenant_id, slack_team_id, APP_TYPE_ONCALL)
    except Exception as e:
        logger.error(
            f'msg="Failed to link slack team: {e}"'
            f"service_tenant_id={service_tenant_id} slack_team_id={slack_team_id}"
        )
        link_slack_team_async.apply_async(
            kwargs={
                "service_tenant_id": service_tenant_id,
                "slack_team_id": slack_team_id,
                "service_type": APP_TYPE_ONCALL,
            },
            countdown=2,
        )


def unlink_slack_team(service_tenant_id: str, slack_team_id: str):
    unlink_slack_team_async.apply_async(
        kwargs={
            "service_tenant_id": service_tenant_id,
            "slack_team_id": slack_team_id,
            "service_type": APP_TYPE_ONCALL,
        }
    )


def uninstall_slack(stack_id: int, grafana_user_id: int) -> bool:
    """
    uninstall_slack uninstalls slack integration from chatops-proxy and returns bool indicating if it was removed.
    If such installation does not exist - returns True as well.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        removed, response = client.delete_oauth_installation(
            stack_id, PROVIDER_TYPE_SLACK, grafana_user_id, APP_TYPE_ONCALL
        )
    except ChatopsProxyAPIException as api_exc:
        if api_exc.status == 404:
            return True
        logger.exception(
            "uninstall_slack: error trying to install slack from chatops-proxy: " "error=%s",
            api_exc,
        )
        return False

    return removed
