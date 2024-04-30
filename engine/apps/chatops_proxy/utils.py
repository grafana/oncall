"""
Set of utils to handle oncall and chatops-proxy interaction.
"""
import logging
import typing

from django.conf import settings
from rest_framework.request import Request

from common.oncall_gateway.tasks import (
    link_slack_team_async,
    register_oncall_tenant_async,
    unlink_slack_team_async,
    unregister_oncall_tenant_async,
)

from .client import SERVICE_TYPE_ONCALL, ChatopsProxyAPIClient

logger = logging.getLogger(__name__)


def get_installation_link_from_chatops_proxy(request: Request) -> typing.Optional[str]:
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)

    try:
        link, _ = client.get_slack_oauth_link(
            request.user.organization.stack_id, request.user.user_id, request.user.organization.web_link
        )
        return link
    except Exception as e:
        logger.exception("Error while getting installation link from chatops proxy: error=%s", e)
        return None


def register_oncall_tenant(service_tenant_id: str, cluster_slug: str, stack_id: int):
    """
    register_oncall_tenant tries to register oncall tenant synchronously and fall back to task in case of any exceptions
    to make sure that tenant is registered.
    First attempt is synchronous to register tenant ASAP to not miss any chatops requests.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.register_tenant(
            service_tenant_id,
            cluster_slug,
            SERVICE_TYPE_ONCALL,
            stack_id,
        )
    except Exception as e:
        logger.error(
            f"create_oncall_connector: failed " f"oncall_org_id={service_tenant_id} backend={cluster_slug} exc={e}"
        )
        register_oncall_tenant_async.apply_async(
            kwargs={
                "service_tenant_id": service_tenant_id,
                "cluster_slug": cluster_slug,
                "service_type": SERVICE_TYPE_ONCALL,
                "stack_id": stack_id,
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
            "service_type": SERVICE_TYPE_ONCALL,
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
        response = client.can_slack_link(service_tenant_id, cluster_slug, slack_team_id, SERVICE_TYPE_ONCALL)
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
        client.link_slack_team(service_tenant_id, slack_team_id, SERVICE_TYPE_ONCALL)
    except Exception as e:
        logger.error(
            f'msg="Failed to link slack team: {e}"'
            f"service_tenant_id={service_tenant_id} slack_team_id={slack_team_id}"
        )
        link_slack_team_async.apply_async(
            kwargs={
                "service_tenant_id": service_tenant_id,
                "slack_team_id": slack_team_id,
                "service_type": SERVICE_TYPE_ONCALL,
            },
            countdown=2,
        )


def unlink_slack_team(service_tenant_id: str, slack_team_id: str):
    unlink_slack_team_async.apply_async(
        kwargs={
            "service_tenant_id": service_tenant_id,
            "slack_team_id": slack_team_id,
            "service_type": SERVICE_TYPE_ONCALL,
        }
    )
