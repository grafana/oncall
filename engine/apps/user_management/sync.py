import logging

from celery.utils.log import get_task_logger
from django.utils import timezone
from rest_framework import status

from apps.grafana_plugin.helpers.client import GcomAPIClient, GrafanaAPIClient
from apps.user_management.models import Organization, Team, User

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def sync_organization(organization):
    client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)

    api_users, call_status = client.get_users()
    status_code = call_status["status_code"]

    # if stack is 404ing, delete the organization in case gcom stack is deleted.
    if status_code == status.HTTP_404_NOT_FOUND:
        is_deleted = delete_organization_if_needed(organization)
        if is_deleted:
            return

    sync_instance_info(organization)

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
            "grafana_url",
            "last_time_synced",
            "api_token_status",
            "gcom_token_org_last_time_synced",
        ]
    )


def sync_instance_info(organization):
    if organization.gcom_token:
        gcom_client = GcomAPIClient(organization.gcom_token)
        instance_info, _ = gcom_client.get_instance_info(organization.stack_id)
        if not instance_info or str(instance_info["orgId"]) != organization.org_id:
            return

        organization.stack_slug = instance_info["slug"]
        organization.org_slug = instance_info["orgSlug"]
        organization.org_title = instance_info["orgName"]
        organization.grafana_url = instance_info["url"]
        organization.gcom_token_org_last_time_synced = timezone.now()


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
    if organization.gcom_token is None:
        return False

    gcom_client = GcomAPIClient(organization.gcom_token)
    is_stack_deleted = gcom_client.is_stack_deleted(organization.stack_id)

    if not is_stack_deleted:
        return False

    logger.info(
        f"Deleting organization due to stack deletion. "
        f"pk: {organization.pk}, stack_id: {organization.stack_id}, org_id: {organization.org_id}"
    )
    organization.delete()

    return True
