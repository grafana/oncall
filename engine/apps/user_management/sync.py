import logging

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.grafana_plugin.helpers.client import GcomAPIClient, GrafanaAPIClient
from apps.user_management.models import Organization, Team, User

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def sync_organization(organization):
    client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)

    rbac_is_enabled = client.is_rbac_enabled_for_organization()
    organization.is_rbac_permissions_enabled = rbac_is_enabled

    if organization.gcom_token:
        gcom_client = GcomAPIClient(organization.gcom_token)
        instance_info = gcom_client.get_instance_info(organization.stack_id)
        if not instance_info or str(instance_info["orgId"]) != organization.org_id:
            return

        organization.stack_slug = instance_info["slug"]
        organization.org_slug = instance_info["orgSlug"]
        organization.org_title = instance_info["orgName"]
        organization.region_slug = instance_info["regionSlug"]
        organization.grafana_url = instance_info["url"]
        organization.gcom_token_org_last_time_synced = timezone.now()

    api_users = client.get_users(rbac_is_enabled)

    if api_users:
        organization.api_token_status = Organization.API_TOKEN_STATUS_OK
        sync_users_and_teams(client, api_users, organization)
    else:
        organization.api_token_status = Organization.API_TOKEN_STATUS_FAILED

    organization.save(
        update_fields=[
            "stack_slug",
            "org_slug",
            "org_title",
            "region_slug",
            "grafana_url",
            "last_time_synced",
            "api_token_status",
            "gcom_token_org_last_time_synced",
            "is_rbac_permissions_enabled",
        ]
    )


def sync_users_and_teams(client, api_users, organization):
    # check if api_users are shaped correctly. e.g. for paused instance, the response is not a list.
    if not api_users or not isinstance(api_users, (tuple, list)):
        return

    User.objects.sync_for_organization(organization=organization, api_users=api_users)

    api_teams_result, _ = client.get_teams()
    if not api_teams_result:
        return

    api_teams = api_teams_result["teams"]
    Team.objects.sync_for_organization(organization=organization, api_teams=api_teams)

    for team in organization.teams.all():
        members, _ = client.get_team_members(team.team_id)
        if not members:
            continue
        User.objects.sync_for_team(team=team, api_members=members)

    organization.last_time_synced = timezone.now()


def delete_organization_if_needed(organization):
    # Organization has a manually set API token, it will not be found within GCOM
    # and would need to be deleted manually.
    if organization.gcom_token is None:
        return False

    # Use common token as organization.gcom_token could be already revoked
    client = GcomAPIClient(settings.GRAFANA_COM_API_TOKEN)
    is_stack_deleted = client.is_stack_deleted(organization.stack_id)
    if not is_stack_deleted:
        return False

    organization.delete()
    return True


def cleanup_organization(organization_pk):
    logger.info(f"Start cleanup Organization {organization_pk}")
    try:
        organization = Organization.objects.get(pk=organization_pk)
        if delete_organization_if_needed(organization):
            logger.info(
                f"Deleting organization due to stack deletion. "
                f"pk: {organization_pk}, stack_id: {organization.stack_id}, org_id: {organization.org_id}"
            )
        else:
            logger.info(f"Organization {organization_pk} not deleted in gcom, no action taken")
    except Organization.DoesNotExist:
        logger.info(f"Organization {organization_pk} was not found")
