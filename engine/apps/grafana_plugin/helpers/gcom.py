import logging
from typing import Optional, Tuple

from django.conf import settings
from django.utils import timezone

from apps.auth_token.exceptions import InvalidToken
from apps.auth_token.models import PluginAuthToken
from apps.grafana_plugin.helpers import GcomAPIClient
from apps.user_management.models import Organization

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
GCOM_TOKEN_CHECK_PERIOD = timezone.timedelta(minutes=60)


class GcomToken:
    def __init__(self, organization):
        self.organization = organization


def check_gcom_permission(token_string: str, context) -> GcomToken:
    """
    Verify that request from plugin is valid. Check it and synchronize the organization details
    with gcom every GCOM_TOKEN_CHECK_PERIOD.
    """

    stack_id = context["stack_id"]
    org_id = context["org_id"]
    organization = Organization.objects.filter(stack_id=stack_id, org_id=org_id).first()
    if (
        organization
        and organization.gcom_token == token_string
        and organization.gcom_token_org_last_time_synced
        and timezone.now() - organization.gcom_token_org_last_time_synced < GCOM_TOKEN_CHECK_PERIOD
    ):
        logger.debug(f"Allow request without calling gcom api for org={org_id}, stack_id={stack_id}")
        return GcomToken(organization)

    logger.debug(f"Start authenticate by making request to gcom api for org={org_id}, stack_id={stack_id}")
    client = GcomAPIClient(token_string)
    instance_info = client.get_instance_info(stack_id)
    if not instance_info or str(instance_info["orgId"]) != org_id:
        raise InvalidToken

    if not organization:
        from apps.base.models import DynamicSetting

        allow_signup = DynamicSetting.objects.get_or_create(
            name="allow_plugin_organization_signup", defaults={"boolean_value": True}
        )[0].boolean_value
        if allow_signup:
            # Get org from db or create a new one
            organization, _ = Organization.objects.get_or_create(
                stack_id=str(instance_info["id"]),
                stack_slug=instance_info["slug"],
                grafana_url=instance_info["url"],
                org_id=str(instance_info["orgId"]),
                org_slug=instance_info["orgSlug"],
                org_title=instance_info["orgName"],
                region_slug=instance_info["regionSlug"],
                cluster_slug=instance_info["clusterSlug"],
                gcom_token=token_string,
                defaults={"gcom_token_org_last_time_synced": timezone.now()},
            )
    else:
        organization.stack_slug = instance_info["slug"]
        organization.org_slug = instance_info["orgSlug"]
        organization.org_title = instance_info["orgName"]
        organization.region_slug = instance_info["regionSlug"]
        organization.grafana_url = instance_info["url"]
        organization.cluster_slug = instance_info["clusterSlug"]
        organization.gcom_token = token_string
        organization.gcom_token_org_last_time_synced = timezone.now()
        organization.save(
            update_fields=[
                "stack_slug",
                "org_slug",
                "org_title",
                "region_slug",
                "grafana_url",
                "gcom_token",
                "gcom_token_org_last_time_synced",
                "cluster_slug",
            ]
        )
    logger.debug(f"Finish authenticate by making request to gcom api for org={org_id}, stack_id={stack_id}")
    return GcomToken(organization)


def check_token(token_string: str, context: dict) -> GcomToken | PluginAuthToken:
    token_parts = token_string.split(":")
    if len(token_parts) > 1 and token_parts[0] == "gcom":
        return check_gcom_permission(token_parts[1], context)
    else:
        return PluginAuthToken.validate_token_string(token_string, context=context)


def get_instance_ids(query: str) -> Tuple[Optional[set], bool]:
    if not settings.GRAFANA_COM_API_TOKEN or settings.LICENSE != settings.CLOUD_LICENSE_NAME:
        return None, False

    client = GcomAPIClient(settings.GRAFANA_COM_API_TOKEN)
    instance_pages = client.get_instances(query, GcomAPIClient.PAGE_SIZE)

    if not instance_pages:
        return None, True

    ids = set(i["id"] for page in instance_pages for i in page["items"])

    return ids, True


def get_active_instance_ids() -> Tuple[Optional[set], bool]:
    return get_instance_ids(GcomAPIClient.ACTIVE_INSTANCE_QUERY)


def get_deleted_instance_ids() -> Tuple[Optional[set], bool]:
    return get_instance_ids(GcomAPIClient.DELETED_INSTANCE_QUERY)


def get_stack_regions() -> Tuple[Optional[set], bool]:
    if not settings.GRAFANA_COM_API_TOKEN or settings.LICENSE != settings.CLOUD_LICENSE_NAME:
        return None, False

    client = GcomAPIClient(settings.GRAFANA_COM_API_TOKEN)
    regions, status = client.get_stack_regions()

    if not regions or "items" not in regions:
        return None, True

    return regions["items"], True
