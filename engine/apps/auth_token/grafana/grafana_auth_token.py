import typing

from apps.auth_token.exceptions import ServiceAccountDoesNotExist
from apps.grafana_plugin.helpers import GrafanaAPIClient
from apps.user_management.models import Organization

SA_ONCALL_API_NAME = "sa-autogen-OnCall"


def find_service_account(
    organization: Organization, service_account_name=SA_ONCALL_API_NAME
) -> typing.Optional["GrafanaAPIClient.Types.GrafanaServiceAccount"]:
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    response, _ = grafana_api_client.get_service_account(service_account_name)
    if response and "serviceAccounts" in response and response["serviceAccounts"]:
        return response["serviceAccounts"][0]
    return None


def create_service_account(
    organization: Organization, name: str, role: str
) -> GrafanaAPIClient.Types.GrafanaServiceAccount:
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    response, _ = grafana_api_client.create_service_account(name, role)
    return response


def create_service_account_token(
    organization: Organization,
    token_name: str,
    seconds_to_live=int | None,
    service_account_name=SA_ONCALL_API_NAME,
) -> typing.Optional[str]:
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    service_account = find_service_account(organization, service_account_name)
    if not service_account:
        raise ServiceAccountDoesNotExist

    response, _ = grafana_api_client.create_service_account_token(service_account["id"], token_name, seconds_to_live)
    if response:
        return response["key"]
    return None


def get_service_account_token_permissions(organization: Organization, token: str) -> typing.Dict[str, typing.List[str]]:
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=token)
    permissions, _ = grafana_api_client.get_service_account_token_permissions()
    return permissions
