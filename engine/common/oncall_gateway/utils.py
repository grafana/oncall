"""
Set of utils to handle oncall and chatops-proxy interaction.
TODO: Once chatops v3 will be released, remove legacy and wrapper functions
"""
import logging

import requests
from django.conf import settings

from .client import SERVICE_TYPE_ONCALL, ChatopsProxyAPIClient
from .legacy_client import OnCallGatewayAPIClient
from .tasks import (
    create_oncall_connector_async,
    create_slack_connector_async_v2,
    delete_oncall_connector_async,
    delete_slack_connector_async_v2,
    link_slack_team_async,
    register_oncall_tenant_async,
    unlink_slack_team_async,
    unregister_oncall_tenant_async,
)

logger = logging.getLogger(__name__)


# Legacy to work with chatops-proxy v1.
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


# utils to work with v3 version
def register_oncall_tenant(service_tenant_id: str, cluster_slug: str):
    """
    register_oncall_tenant tries to register oncall tenant synchronously and fall back to task in case of any exceptions
    to make sure that tenant is registered.
    First attempt is synchronous to register tenant ASAP to not miss any chatops requests.
    """
    client = ChatopsProxyAPIClient(settings.ONCALL_GATEWAY_URL, settings.ONCALL_GATEWAY_API_TOKEN)
    try:
        client.register_tenant(service_tenant_id, cluster_slug, SERVICE_TYPE_ONCALL)
    except Exception as e:
        logger.error(
            f"create_oncall_connector: failed " f"oncall_org_id={service_tenant_id} backend={cluster_slug} exc={e}"
        )
        register_oncall_tenant_async.apply_async(
            kwargs={
                "service_tenant_id": service_tenant_id,
                "cluster_slug": cluster_slug,
                "service_type": SERVICE_TYPE_ONCALL,
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


# Wrappers to choose whether legacy or v3 function should be call, depending on CHATOPS_V3 env var.
def register_oncall_tenant_wrapper(service_tenant_id: str, cluster_slug: str):
    if settings.CHATOPS_V3:
        register_oncall_tenant(service_tenant_id, cluster_slug)
    else:
        create_oncall_connector(service_tenant_id, cluster_slug)


def unregister_oncall_tenant_wrapper(service_tenant_id: str, cluster_slug: str):
    if settings.CHATOPS_V3:
        unregister_oncall_tenant(service_tenant_id, cluster_slug)
    else:
        delete_oncall_connector(service_tenant_id)


def can_link_slack_team_wrapper(service_tenant_id: str, slack_team_id, cluster_slug: str) -> bool:
    if settings.CHATOPS_V3:
        return can_link_slack_team(service_tenant_id, slack_team_id, cluster_slug)
    else:
        return check_slack_installation_possible(service_tenant_id, slack_team_id, cluster_slug)


def link_slack_team_wrapper(service_tenant_id: str, slack_team_id: str):
    if settings.CHATOPS_V3:
        link_slack_team(service_tenant_id, slack_team_id)
    else:
        create_slack_connector(service_tenant_id, slack_team_id, settings.ONCALL_BACKEND_REGION)


def unlink_slack_team_wrapper(service_tenant_id: str, slack_team_id: str):
    if settings.CHATOPS_V3:
        unlink_slack_team(service_tenant_id, slack_team_id)
    else:
        delete_slack_connector(service_tenant_id)
