import typing

INTEGRATION_INSTALLED_EVENT_TYPE = "integration_installed"
INTEGRATION_UNINSTALLED_EVENT_TYPE = "integration_uninstalled"


class Event(typing.TypedDict):
    event_type: str
    data: dict


class IntegrationInstalledData(typing.TypedDict):
    oauth_installation_id: int
    provider_type: str
    stack_id: int
    grafana_user_id: int
    payload: dict


class IntegrationUninstalledData(typing.TypedDict):
    provider_type: str
    stack_id: int
    grafana_user_id: int
