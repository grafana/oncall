import logging
from typing import Optional, Tuple

from django.apps import apps
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


def check_gcom_permission(token_string: str, context) -> Optional["GcomToken"]:
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
    instance_info, status = client.get_instance_info(stack_id)
    if not instance_info or str(instance_info["orgId"]) != org_id:
        raise InvalidToken

    if not organization:
        DynamicSetting = apps.get_model("base", "DynamicSetting")
        allow_signup = DynamicSetting.objects.get_or_create(
            name="allow_plugin_organization_signup", defaults={"boolean_value": True}
        )[0].boolean_value
        if allow_signup:
            organization = Organization.objects.create(
                stack_id=str(instance_info["id"]),
                stack_slug=instance_info["slug"],
                grafana_url=instance_info["url"],
                org_id=str(instance_info["orgId"]),
                org_slug=instance_info["orgSlug"],
                org_title=instance_info["orgName"],
                gcom_token=token_string,
                gcom_token_org_last_time_synced=timezone.now(),
            )
    else:
        organization.stack_slug = instance_info["slug"]
        organization.org_slug = instance_info["orgSlug"]
        organization.org_title = instance_info["orgName"]
        organization.grafana_url = instance_info["url"]
        organization.gcom_token = token_string
        organization.gcom_token_org_last_time_synced = timezone.now()
        organization.save(
            update_fields=[
                "stack_slug",
                "org_slug",
                "org_title",
                "grafana_url",
                "gcom_token",
                "gcom_token_org_last_time_synced",
            ]
        )
    logger.debug(f"Finish authenticate by making request to gcom api for org={org_id}, stack_id={stack_id}")
    return GcomToken(organization)


def check_token(token_string: str, context: dict):
    token_parts = token_string.split(":")
    if len(token_parts) > 1 and token_parts[0] == "gcom":
        return check_gcom_permission(token_parts[1], context)
    else:
        return PluginAuthToken.validate_token_string(token_string, context=context)


def get_instance_ids(query: str) -> Tuple[Optional[set], bool]:
    if not settings.GRAFANA_COM_API_TOKEN or settings.LICENSE != settings.CLOUD_LICENSE_NAME:
        return None, False

    client = GcomAPIClient(settings.GRAFANA_COM_API_TOKEN)
    instances, status = client.get_instances(query)

    if not instances:
        return None, True

    ids = set(i["id"] for i in instances["items"])
    return ids, True


def get_active_instance_ids() -> Tuple[Optional[set], bool]:
    return get_instance_ids(GcomAPIClient.ACTIVE_INSTANCE_QUERY)


def get_deleted_instance_ids() -> Tuple[Optional[set], bool]:
    return get_instance_ids(GcomAPIClient.DELETED_INSTANCE_QUERY)
