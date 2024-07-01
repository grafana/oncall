import logging
import uuid

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.grafana_plugin.helpers.client import GcomAPIClient, GrafanaAPIClient
from apps.user_management.models import Organization, Team, User
from apps.user_management.signals import org_sync_signal
from common.utils import task_lock

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def sync_organization(organization: Organization) -> None:
    # ensure one sync task is running at most for a given org at a given time
    lock_id = "sync-organization-lock-{}".format(organization.id)
    random_value = str(uuid.uuid4())
    with task_lock(lock_id, random_value) as acquired:
        if acquired:
            _sync_organization(organization)
        else:
            # sync already running
            logger.info(f"Sync for Organization {organization.pk} already in progress.")


def _sync_organization(organization: Organization) -> None:
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    rbac_is_enabled = organization.is_rbac_permissions_enabled

    # NOTE: checking whether or not RBAC is enabled depends on whether we are dealing with an open-source or cloud
    # stack. For open-source, simply make a HEAD request to the grafana instance's API and consider RBAC enabled if
    # the list RBAC permissions endpoint returns 200.
    #
    # For cloud, we need to check the stack's status first. If the stack is active, we can make the same HEAD request
    # to the grafana instance's API. If the stack is not active, we will simply rely on the org's previous state of
    # org.is_rbac_permissions_enabled
    if settings.LICENSE == settings.CLOUD_LICENSE_NAME:
        # We cannot simply rely on the HEAD call in cloud because if an instance is not active
        # the grafana gateway will still return 200 for the HEAD request.
        stack_id = organization.stack_id
        gcom_client = GcomAPIClient(settings.GRAFANA_COM_ADMIN_API_TOKEN)

        if gcom_client.is_stack_active(stack_id):
            # the stack MUST be active for this check.. if it is in any other state
            # the Grafana API risks returning an HTTP 200 but the actual permissions data that is
            # synced later on will be empty (and we'd erase all RBAC permissions stored in OnCall)
            rbac_is_enabled = grafana_api_client.is_rbac_enabled_for_organization()
    else:
        rbac_is_enabled = grafana_api_client.is_rbac_enabled_for_organization()

    organization.is_rbac_permissions_enabled = rbac_is_enabled
    logger.info(f"RBAC status org={organization.pk} rbac_enabled={organization.is_rbac_permissions_enabled}")

    _sync_instance_info(organization)

    _, check_token_call_status = grafana_api_client.check_token()
    if check_token_call_status["connected"]:
        organization.api_token_status = Organization.API_TOKEN_STATUS_OK
        sync_users_and_teams(grafana_api_client, organization)
        organization.last_time_synced = timezone.now()

        _sync_grafana_incident_plugin(organization, grafana_api_client)
        _sync_grafana_labels_plugin(organization, grafana_api_client)
    else:
        organization.api_token_status = Organization.API_TOKEN_STATUS_FAILED
        logger.warning(f"Sync not successful org={organization.pk} token_status=FAILED")

    organization.save(
        update_fields=[
            "cluster_slug",
            "stack_slug",
            "org_slug",
            "org_title",
            "region_slug",
            "grafana_url",
            "last_time_synced",
            "api_token_status",
            "gcom_token_org_last_time_synced",
            "is_rbac_permissions_enabled",
            "is_grafana_incident_enabled",
            "is_grafana_labels_enabled",
            "grafana_incident_backend_url",
        ]
    )

    org_sync_signal.send(sender=None, organization=organization)


def _sync_instance_info(organization: Organization) -> None:
    if organization.gcom_token:
        gcom_client = GcomAPIClient(organization.gcom_token)
        instance_info = gcom_client.get_instance_info(organization.stack_id)

        if not instance_info or instance_info["orgId"] != organization.org_id:
            return

        organization.stack_slug = instance_info["slug"]
        organization.org_slug = instance_info["orgSlug"]
        organization.org_title = instance_info["orgName"]
        organization.region_slug = instance_info["regionSlug"]
        organization.grafana_url = instance_info["url"]
        organization.cluster_slug = instance_info["clusterSlug"]
        organization.gcom_token_org_last_time_synced = timezone.now()


def _sync_grafana_labels_plugin(organization: Organization, grafana_api_client) -> None:
    """
    _sync_grafana_labels_plugin checks if grafana-labels-app plugin is enabled and sets a flag in the organization.
    It intended to use only inside _sync_organization. It mutates, but not saves org, it's saved in _sync_organization.
    """
    grafana_labels_plugin_settings, _ = grafana_api_client.get_grafana_labels_plugin_settings()
    if grafana_labels_plugin_settings is not None:
        organization.is_grafana_labels_enabled = grafana_labels_plugin_settings["enabled"]


def _sync_grafana_incident_plugin(organization: Organization, grafana_api_client) -> None:
    """
    _sync_grafana_incident_plugin check if incident plugin is enabled and sets a flag and its url in the organization.
    It intended to use only inside _sync_organization. It mutates, but not saves org, it's saved in _sync_organization.
    """
    grafana_incident_settings, _ = grafana_api_client.get_grafana_incident_plugin_settings()
    organization.is_grafana_incident_enabled = False
    organization.grafana_incident_backend_url = None

    if grafana_incident_settings is not None:
        organization.is_grafana_incident_enabled = grafana_incident_settings["enabled"]
        organization.grafana_incident_backend_url = (grafana_incident_settings.get("jsonData") or {}).get(
            GrafanaAPIClient.GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY
        )


def sync_users_and_teams(client: GrafanaAPIClient, organization: Organization) -> None:
    sync_users(client, organization)
    sync_teams(client, organization)
    sync_team_members(client, organization)


def sync_users(client: GrafanaAPIClient, organization: Organization, **kwargs) -> None:
    api_users = client.get_users(organization.is_rbac_permissions_enabled, **kwargs)
    # check if api_users are shaped correctly. e.g. for paused instance, the response is not a list.
    if not api_users or not isinstance(api_users, (tuple, list)):
        return
    User.objects.sync_for_organization(organization=organization, api_users=api_users)


def sync_teams(client: GrafanaAPIClient, organization: Organization, **kwargs) -> None:
    api_teams_result, _ = client.get_teams(**kwargs)
    if not api_teams_result:
        return
    api_teams = api_teams_result["teams"]
    Team.objects.sync_for_organization(organization=organization, api_teams=api_teams)


def sync_team_members(client: GrafanaAPIClient, organization: Organization) -> None:
    for team in organization.teams.all():
        members, _ = client.get_team_members(team.team_id)
        if not members:
            continue
        User.objects.sync_for_team(team=team, api_members=members)


def sync_users_for_teams(client: GrafanaAPIClient, organization: Organization, **kwargs) -> None:
    api_teams_result, _ = client.get_teams(**kwargs)
    if not api_teams_result:
        return
    api_teams = api_teams_result["teams"]
    Team.objects.sync_for_organization(organization=organization, api_teams=api_teams)


def delete_organization_if_needed(organization: Organization) -> bool:
    # Organization has a manually set API token, it will not be found within GCOM
    # and would need to be deleted manually.
    from apps.auth_token.models import PluginAuthToken

    manually_provisioned_token = PluginAuthToken.objects.filter(organization_id=organization.pk).first()
    if manually_provisioned_token:
        logger.info(f"Organization {organization.pk} has PluginAuthToken. Probably it's needed to delete org manually.")
        return False

    # Use common token as organization.gcom_token could be already revoked
    client = GcomAPIClient(settings.GRAFANA_COM_ADMIN_API_TOKEN)
    is_stack_deleted = client.is_stack_deleted(organization.stack_id)
    if not is_stack_deleted:
        return False

    organization.delete()
    return True


def cleanup_organization(organization_pk: int) -> None:
    logger.info(f"Start cleanup Organization {organization_pk}")
    try:
        organization = Organization.objects_with_deleted.get(pk=organization_pk)

        from apps.grafana_plugin.tasks.sync import cleanup_empty_deleted_integrations

        cleanup_empty_deleted_integrations.apply_async(
            (
                organization.pk,
                False,
            ),
        )

        if delete_organization_if_needed(organization):
            logger.info(
                f"Deleting organization due to stack deletion. "
                f"pk: {organization_pk}, stack_id: {organization.stack_id}, org_id: {organization.org_id}"
            )
        else:
            logger.info(f"Organization {organization_pk} not deleted in gcom, no action taken")

    except Organization.DoesNotExist:
        logger.info(f"Organization {organization_pk} was not found")
