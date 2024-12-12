import logging
import typing
import uuid

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole
from apps.auth_token.exceptions import InvalidToken
from apps.grafana_plugin.helpers.client import GcomAPIClient, GCOMInstanceInfo, GrafanaAPIClient
from apps.grafana_plugin.sync_data import SyncData, SyncPermission, SyncSettings, SyncTeam, SyncUser
from apps.metrics_exporter.helpers import metrics_bulk_update_team_label_cache
from apps.metrics_exporter.metrics_cache_manager import MetricsCacheManager
from apps.user_management.models import Organization, Team, User
from common.utils import task_lock
from settings.base import CLOUD_LICENSE_NAME, OPEN_SOURCE_LICENSE_NAME

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
    gcom_client = GcomAPIClient(settings.GRAFANA_COM_ADMIN_API_TOKEN)

    # check organization API token is valid
    _, check_token_call_status = grafana_api_client.check_token()
    if not check_token_call_status["connected"]:
        organization.api_token_status = Organization.API_TOKEN_STATUS_FAILED
        organization.save(update_fields=["api_token_status"])
        logger.warning(f"Sync not successful org={organization.pk} token_status=FAILED")
        return

    rbac_is_enabled = organization.is_rbac_permissions_enabled
    # Update organization's RBAC status if it's an open-source instance, or it's an active cloud instance.
    # Don't update non-active cloud instances (e.g. paused) as they can return 200 OK but not have RBAC enabled.
    if settings.LICENSE == settings.OPEN_SOURCE_LICENSE_NAME or gcom_client.is_stack_active(organization.stack_id):
        rbac_enabled_update, server_error = grafana_api_client.is_rbac_enabled_for_organization()
        if not server_error:  # Only update RBAC status if Grafana didn't return a server error
            rbac_is_enabled = rbac_enabled_update

    # get incident plugin settings
    grafana_incident_settings, _ = grafana_api_client.get_grafana_incident_plugin_settings()
    is_grafana_incident_enabled = False
    grafana_incident_backend_url = None
    if grafana_incident_settings is not None:
        is_grafana_incident_enabled = grafana_incident_settings["enabled"]
        grafana_incident_backend_url = (grafana_incident_settings.get("jsonData") or {}).get(
            GrafanaAPIClient.GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY
        )

    # get labels plugin settings
    is_grafana_labels_enabled = False
    grafana_labels_plugin_settings, _ = grafana_api_client.get_grafana_labels_plugin_settings()
    if grafana_labels_plugin_settings is not None:
        is_grafana_labels_enabled = grafana_labels_plugin_settings["enabled"]

    # get IRM plugin settings
    is_grafana_irm_enabled = False
    grafana_irm_plugin_settings, _ = grafana_api_client.get_grafana_irm_plugin_settings()
    if grafana_irm_plugin_settings is not None:
        is_grafana_irm_enabled = grafana_irm_plugin_settings["enabled"]

    oncall_api_url = settings.BASE_URL
    if settings.LICENSE == CLOUD_LICENSE_NAME:
        oncall_api_url = settings.GRAFANA_CLOUD_ONCALL_API_URL

    sync_settings = SyncSettings(
        stack_id=organization.stack_id,
        org_id=organization.org_id,
        license=settings.LICENSE,
        oncall_api_url=oncall_api_url,
        oncall_token=organization.gcom_token,
        grafana_url=organization.grafana_url,
        grafana_token=organization.api_token,
        rbac_enabled=rbac_is_enabled,
        incident_enabled=is_grafana_incident_enabled,
        incident_backend_url=grafana_incident_backend_url,
        labels_enabled=is_grafana_labels_enabled,
        irm_enabled=is_grafana_irm_enabled,
    )
    _sync_organization_data(organization, sync_settings)
    if organization.api_token_status == Organization.API_TOKEN_STATUS_OK:
        sync_users_and_teams(grafana_api_client, organization)


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


def sync_users_and_teams(client: GrafanaAPIClient, organization: Organization) -> None:
    sync_users(client, organization)
    sync_teams(client, organization)
    sync_team_members(client, organization)


def sync_users(client: GrafanaAPIClient, organization: Organization, **kwargs) -> None:
    api_users = client.get_users(organization.is_rbac_permissions_enabled, **kwargs)
    # check if api_users are shaped correctly. e.g. for paused instance, the response is not a list.
    if not api_users or not isinstance(api_users, (tuple, list)):
        return

    sync_users = [
        SyncUser(
            id=user["userId"],
            name=user["name"],
            login=user["login"],
            email=user["email"],
            role=user["role"],
            avatar_url=user["avatarUrl"],
            teams=None,
            permissions=[SyncPermission(action=permission["action"]) for permission in user["permissions"]],
        )
        for user in api_users
    ]
    _sync_users_data(organization, sync_users, delete_extra=True)


def sync_teams(client: GrafanaAPIClient, organization: Organization, **kwargs) -> None:
    api_teams_result, _ = client.get_teams(**kwargs)
    if not api_teams_result:
        return
    api_teams = api_teams_result["teams"]
    sync_teams = [
        SyncTeam(
            team_id=team["id"],
            name=team["name"],
            email=team["email"],
            avatar_url=team["avatarUrl"],
        )
        for team in api_teams
    ]
    _sync_teams_data(organization, sync_teams)


def sync_team_members(client: GrafanaAPIClient, organization: Organization) -> None:
    team_members = {}
    for team in organization.teams.all():
        members, _ = client.get_team_members(team.team_id)
        if not members:
            continue
        team_members[team.team_id] = [member["userId"] for member in members]
    _sync_teams_members_data(organization, team_members)


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


def _create_cloud_organization(
    org_id: int, stack_id: int, sync_data: SyncData, instance_info: GCOMInstanceInfo
) -> Organization:
    client = GcomAPIClient(sync_data.settings.oncall_token)
    if not instance_info:
        instance_info = client.get_instance_info(stack_id)
        if not instance_info or str(instance_info["orgId"]) != org_id:
            raise InvalidToken

    return Organization.objects.create(
        stack_id=str(instance_info["id"]),
        stack_slug=instance_info["slug"],
        grafana_url=instance_info["url"],
        org_id=str(instance_info["orgId"]),
        org_slug=instance_info["orgSlug"],
        org_title=instance_info["orgName"],
        region_slug=instance_info["regionSlug"],
        cluster_slug=instance_info["clusterSlug"],
        api_token=sync_data.settings.grafana_token,
        gcom_token=sync_data.settings.oncall_token,
        is_rbac_permissions_enabled=sync_data.settings.rbac_enabled,
        defaults={"gcom_token_org_last_time_synced": timezone.now()},
    )


def _create_oss_organization(sync_data: SyncData) -> Organization:
    return Organization.objects.create(
        stack_id=settings.SELF_HOSTED_SETTINGS["STACK_ID"],
        stack_slug=settings.SELF_HOSTED_SETTINGS["STACK_SLUG"],
        org_id=settings.SELF_HOSTED_SETTINGS["ORG_ID"],
        org_slug=settings.SELF_HOSTED_SETTINGS["ORG_SLUG"],
        org_title=settings.SELF_HOSTED_SETTINGS["ORG_TITLE"],
        region_slug=settings.SELF_HOSTED_SETTINGS["REGION_SLUG"],
        cluster_slug=settings.SELF_HOSTED_SETTINGS["CLUSTER_SLUG"],
        grafana_url=sync_data.settings.grafana_url,
        api_token=sync_data.settings.grafana_token,
        is_rbac_permissions_enabled=sync_data.settings.rbac_enabled,
    )


def _create_organization(
    org_id: int, stack_id: int, sync_data: SyncData, instance_info: GCOMInstanceInfo
) -> typing.Optional[Organization]:
    if settings.LICENSE == CLOUD_LICENSE_NAME:
        return _create_cloud_organization(org_id, stack_id, sync_data, instance_info)
    elif settings.LICENSE == OPEN_SOURCE_LICENSE_NAME:
        return _create_oss_organization(sync_data)
    return None


def get_or_create_organization(
    org_id: int, stack_id: int, sync_data: SyncData = None, instance_info: GCOMInstanceInfo = None
) -> Organization:
    organization = Organization.objects.filter(org_id=org_id, stack_id=stack_id).first()
    if not organization:
        organization = _create_organization(org_id, stack_id, sync_data, instance_info)
    return organization


def get_or_create_user(organization: Organization, sync_user: SyncUser) -> User:
    _sync_users_data(organization, [sync_user], delete_extra=False)
    user = organization.users.get(user_id=sync_user.id)

    # update team membership if needed
    # (not removing user from teams, assuming this is called on user creation/first login only;
    # periodic sync will keep teams updated)
    membership = sync_user.teams or []
    for team_id in membership:
        team = organization.teams.filter(team_id=team_id).first()
        if team:
            user.teams.add(team)

    return user


def _sync_organization_data(organization: Organization, sync_settings: SyncSettings):
    organization.is_rbac_permissions_enabled = sync_settings.rbac_enabled
    logger.info(f"RBAC status org={organization.pk} rbac_enabled={organization.is_rbac_permissions_enabled}")

    organization.is_grafana_irm_enabled = sync_settings.irm_enabled
    organization.is_grafana_labels_enabled = sync_settings.labels_enabled
    organization.is_grafana_incident_enabled = sync_settings.incident_enabled
    organization.grafana_incident_backend_url = sync_settings.incident_backend_url
    organization.grafana_url = sync_settings.grafana_url
    organization.api_token = sync_settings.grafana_token
    organization.last_time_synced = timezone.now()

    _sync_instance_info(organization)

    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    _, check_token_call_status = grafana_api_client.check_token()
    if check_token_call_status["connected"]:
        organization.api_token_status = Organization.API_TOKEN_STATUS_OK
        organization.last_time_synced = timezone.now()
    else:
        organization.api_token_status = Organization.API_TOKEN_STATUS_FAILED
        logger.warning(f"Sync not successful org={organization.pk} token_status=FAILED")

    organization.save(
        update_fields=[
            "api_token",
            "api_token_status",
            "cluster_slug",
            "stack_slug",
            "org_slug",
            "org_title",
            "region_slug",
            "grafana_url",
            "last_time_synced",
            "gcom_token_org_last_time_synced",
            "is_rbac_permissions_enabled",
            "is_grafana_incident_enabled",
            "is_grafana_labels_enabled",
            "is_grafana_irm_enabled",
            "grafana_incident_backend_url",
        ]
    )


def _sync_users_data(organization: Organization, sync_users: list[SyncUser], delete_extra=False):
    if sync_users is None:
        return
    users_to_sync = (
        User(
            organization_id=organization.pk,
            user_id=user.id,
            email=user.email,
            name=user.name,
            username=user.login,
            role=getattr(LegacyAccessControlRole, user.role.upper(), LegacyAccessControlRole.NONE),
            avatar_url=user.avatar_url,
            permissions=[{"action": permission.action} for permission in user.permissions] if user.permissions else [],
        )
        for user in sync_users
    )

    existing_user_ids = set(organization.users.all().values_list("user_id", flat=True))
    kwargs = {}
    if settings.DATABASE_TYPE in ("sqlite3", "postgresql"):
        # unique_fields is required for sqlite and postgresql setups
        kwargs["unique_fields"] = ("organization_id", "user_id", "is_active")
    organization.users.bulk_create(
        users_to_sync,
        update_conflicts=True,
        update_fields=("email", "name", "username", "role", "avatar_url", "permissions"),
        batch_size=5000,
        **kwargs,
    )

    # Retrieve primary keys for the newly created users
    #
    # If the model’s primary key is an AutoField, the primary key attribute can only be retrieved
    # on certain databases (currently PostgreSQL, MariaDB 10.5+, and SQLite 3.35+).
    # On other databases, it will not be set.
    # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#django.db.models.query.QuerySet.bulk_create
    created_users = organization.users.exclude(user_id__in=existing_user_ids)

    if delete_extra:
        # delete removed users
        existing_user_ids |= set(u.user_id for u in created_users)
        user_ids_to_delete = existing_user_ids - {user.id for user in sync_users}
        organization.users.filter(user_id__in=user_ids_to_delete).delete()


def _sync_teams_data(organization: Organization, sync_teams: list[SyncTeam] | None):
    if sync_teams is None:
        sync_teams = []
    # keep existing team names mapping to check for possible metrics cache updates
    existing_team_names = {team.team_id: team.name for team in organization.teams.all()}
    teams_to_sync = tuple(
        Team(
            organization_id=organization.pk,
            team_id=team.team_id,
            name=team.name,
            email=team.email,
            avatar_url=team.avatar_url,
        )
        for team in sync_teams
    )
    # create entries, update if team_id already exists in the organization
    kwargs = {}
    if settings.DATABASE_TYPE in ("sqlite3", "postgresql"):
        # unique_fields is required for sqlite and postgresql setups
        kwargs["unique_fields"] = ("organization_id", "team_id")
    organization.teams.bulk_create(
        teams_to_sync,
        batch_size=5000,
        update_conflicts=True,
        update_fields=("name", "email", "avatar_url"),
        **kwargs,
    )

    # create missing direct paging integrations
    AlertReceiveChannel.objects.create_missing_direct_paging_integrations(organization)

    # delete removed teams and their direct paging integrations
    existing_team_ids = set(organization.teams.all().values_list("team_id", flat=True))
    team_ids_to_delete = existing_team_ids - set(t.team_id for t in sync_teams)
    organization.alert_receive_channels.filter(
        team__team_id__in=team_ids_to_delete, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
    ).delete()
    organization.teams.filter(team_id__in=team_ids_to_delete).delete()

    # collect teams diffs to update metrics cache
    metrics_teams_to_update: MetricsCacheManager.TeamsDiffMap = {}
    for team_id in team_ids_to_delete:
        metrics_teams_to_update = MetricsCacheManager.update_team_diff(metrics_teams_to_update, team_id, deleted=True)
    for team in sync_teams:
        previous_name = existing_team_names.get(team.team_id)
        if previous_name and previous_name != team.name:
            metrics_teams_to_update = MetricsCacheManager.update_team_diff(
                metrics_teams_to_update, team.team_id, new_name=team.name
            )
    metrics_bulk_update_team_label_cache(metrics_teams_to_update, organization.id)


def _sync_teams_members_data(organization: Organization, team_members: dict[int, list[int]] | None):
    if team_members is None:
        return
    # set team members
    for team_id, members_ids in team_members.items():
        team = organization.teams.get(team_id=team_id)
        if members_ids:
            team.users.set(organization.users.filter(user_id__in=members_ids))
        else:
            team.users.clear()


def apply_sync_data(organization: Organization, sync_data: SyncData):
    # update org + settings
    _sync_organization_data(organization, sync_data.settings)
    # update or create users
    _sync_users_data(organization, sync_data.users, delete_extra=True)
    # update or create teams + direct paging integrations
    _sync_teams_data(organization, sync_data.teams)
    # update team members
    _sync_teams_members_data(organization, sync_data.team_members)
