import logging

import requests
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import IsAdmin, MethodPermission
from apps.auth_token.auth import PluginAuthentication
from apps.migration_tool.constants import FINISHED, IN_PROGRESS, NOT_STARTED, REQUEST_URL
from apps.migration_tool.tasks import start_migration_from_old_amixr
from apps.migration_tool.utils import get_data_with_respect_to_pagination
from common.api_helpers.exceptions import BadRequest

logger = logging.getLogger(__name__)


class MigrationPlanAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, MethodPermission)

    method_permissions = {IsAdmin: ("POST",)}

    def post(self, request):
        api_token = request.data.get("token", None)
        if api_token is None:
            raise BadRequest(detail="API token is required")

        organization = request.auth.organization
        if organization.is_amixr_migration_started:
            raise BadRequest(detail="Migration from Amixr has already been started")

        # check token
        response = requests.get(f"{REQUEST_URL}/users", headers={"AUTHORIZATION": api_token})
        if response.status_code == status.HTTP_403_FORBIDDEN:
            raise BadRequest(detail="Invalid token")

        # Just not to re-make the frontend...
        USERS_NOT_TO_MIGRATE_KEY = (
            "Users WON'T be migrated (couldn't find those users in the Grafana Cloud, ask "
            "them to sign up if you want their data to be migrated and re-build the migration plan)"
        )

        USERS_TO_MIGRATE = "Users will be migrated"
        INTEGRATIONS_TO_MIGRATE = "Integrations to migrate"
        INTEGRATIONS_COUNT = "Integrations count"
        ROUTES_COUNT = "Routes count"
        ESCALATIONS_POLICIES_COUNT = "Escalation policies count"
        CALENDARS_COUNT = "Calendars count"

        migration_plan = {
            USERS_TO_MIGRATE: [],
            USERS_NOT_TO_MIGRATE_KEY: [],
            INTEGRATIONS_TO_MIGRATE: [],
            INTEGRATIONS_COUNT: 0,
            ROUTES_COUNT: 0,
            ESCALATIONS_POLICIES_COUNT: 0,
            CALENDARS_COUNT: 0,
        }
        logger.info(f"migration plan for organization {organization.pk}: get users")
        users = get_data_with_respect_to_pagination(api_token, "users")
        logger.info(f"migration plan for organization {organization.pk}: got users")
        org_users = organization.users.values_list("email", flat=True)
        for user in users:
            if user["email"] in org_users:
                migration_plan[USERS_TO_MIGRATE].append(user["email"])
            else:
                migration_plan[USERS_NOT_TO_MIGRATE_KEY].append(user["email"])

        logger.info(f"migration plan for organization {organization.pk}: get integrations")
        integrations = get_data_with_respect_to_pagination(api_token, "integrations")
        logger.info(f"migration plan for organization {organization.pk}: got integrations")
        existing_integrations_names = set(organization.alert_receive_channels.values_list("verbal_name", flat=True))

        integrations_to_migrate_public_pk = []

        for integration in integrations:
            if integration["name"] in existing_integrations_names:
                continue

            try:
                integration_type = [
                    key
                    for key, value in AlertReceiveChannel.INTEGRATIONS_TO_REVERSE_URL_MAP.items()
                    if value == integration["type"]
                ][0]
            except IndexError:
                continue
            if integration_type not in AlertReceiveChannel.WEB_INTEGRATION_CHOICES:
                continue

            migration_plan[INTEGRATIONS_TO_MIGRATE].append(integration["name"])
            integrations_to_migrate_public_pk.append(integration["id"])

        migration_plan[INTEGRATIONS_COUNT] = len(migration_plan[INTEGRATIONS_TO_MIGRATE])

        routes_to_migrate_public_pk = []
        logger.info(f"migration plan for organization {organization.pk}: get routes")
        routes = get_data_with_respect_to_pagination(api_token, "routes")
        logger.info(f"migration plan for organization {organization.pk}: got routes")

        for route in routes:
            if route["integration_id"] in integrations_to_migrate_public_pk:
                migration_plan[ROUTES_COUNT] += 1
                routes_to_migrate_public_pk.append(route["id"])

        logger.info(f"migration plan for organization {organization.pk}: get escalation_policies")
        escalation_policies = get_data_with_respect_to_pagination(api_token, "escalation_policies")
        logger.info(f"migration plan for organization {organization.pk}: got escalation_policies")

        for escalation_policy in escalation_policies:
            if escalation_policy["route_id"] in routes_to_migrate_public_pk:
                migration_plan[ESCALATIONS_POLICIES_COUNT] += 1

        logger.info(f"migration plan for organization {organization.pk}: get schedules")
        schedules = get_data_with_respect_to_pagination(api_token, "schedules")
        logger.info(f"migration plan for organization {organization.pk}: got schedules")

        existing_schedules_names = set(organization.oncall_schedules.values_list("name", flat=True))
        for schedule in schedules:
            if not schedule["ical_url"] or schedule["name"] in existing_schedules_names:
                continue
            migration_plan[CALENDARS_COUNT] += 1

        return Response(migration_plan)


class MigrateAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def post(self, request):
        api_token = request.data.get("token", None)

        if api_token is None:
            raise BadRequest(detail="API token is required")

        organization = request.auth.organization
        if organization.is_amixr_migration_started:
            raise BadRequest(detail="Migration from Amixr has already been started")
        # check token
        response = requests.get(f"{REQUEST_URL}/users", headers={"AUTHORIZATION": api_token})
        if response.status_code == status.HTTP_403_FORBIDDEN:
            raise BadRequest(detail="Invalid token")

        organization.is_amixr_migration_started = True
        organization.save(update_fields=["is_amixr_migration_started"])

        organization_id = organization.pk
        user_id = request.user.pk
        # start migration process
        start_migration_from_old_amixr.delay(api_token=api_token, organization_id=organization_id, user_id=user_id)
        return Response(status=status.HTTP_200_OK)


class MigrationStatusAPIView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        organization = request.auth.organization
        migration_status = self.get_migration_status(organization)
        endpoints_list = self.get_endpoints_list(organization)
        return Response(
            {"migration_status": migration_status, "endpoints_list": endpoints_list}, status=status.HTTP_200_OK
        )

    def get_migration_status(self, organization):
        migration_status = NOT_STARTED
        if organization.is_amixr_migration_started:
            unfinished_tasks_exist = organization.migration_tasks.filter(is_finished=False).exists()
            if unfinished_tasks_exist:
                migration_status = IN_PROGRESS
            else:
                migration_status = FINISHED
        return migration_status

    def get_endpoints_list(self, organization):
        integrations = organization.alert_receive_channels.filter(team_id__isnull=True)
        endpoints_list = []
        for integration in integrations:
            integration_endpoint = f"{integration.verbal_name}, new endpoint: {integration.integration_url}"
            endpoints_list.append(integration_endpoint)
        return endpoints_list
