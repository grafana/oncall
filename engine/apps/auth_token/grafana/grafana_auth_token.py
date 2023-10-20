from apps.auth_token.exceptions import ServiceAccountDoesNotExist
from apps.grafana_plugin.helpers import GrafanaAPIClient

SA_ONCALL_API_NAME = "OnCall API"
SA_ONCALL_API_LOGIN = "sa-oncall-api"


def get_service_account(organization, service_account_login):
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    response, _ = grafana_api_client.get_service_account(service_account_login)
    if response and "serviceAccounts" in response and response["serviceAccounts"]:
        return response["serviceAccounts"][0]
    return None


def create_service_account(organization, name, role):
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    response, _ = grafana_api_client.create_service_account(name, role)
    return response


def create_service_account_token(organization, service_account_login, token_name, seconds_to_live=None):
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
    service_account = get_service_account(organization, service_account_login)
    if not service_account:
        raise ServiceAccountDoesNotExist

    response, _ = grafana_api_client.create_service_account_token(service_account["id"], token_name, seconds_to_live)
    if response:
        return response["key"]
    return None


def get_service_account_token_permissions(organization, token):
    grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=token)
    permissions, _ = grafana_api_client.get_service_account_token_permissions()
    return permissions
