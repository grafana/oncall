import json
import logging
import time
import typing
from urllib.parse import urljoin

import requests
from django.conf import settings
from rest_framework import status

from apps.api.permissions import ACTION_PREFIX, GrafanaAPIPermission

logger = logging.getLogger(__name__)


class GrafanaUser(typing.TypedDict):
    orgId: int
    userId: int
    email: str
    name: str
    avatarUrl: str
    login: str
    role: str
    lastSeenAt: str
    lastSeenAtAge: str


class GrafanaUserWithPermissions(GrafanaUser):
    permissions: typing.List[GrafanaAPIPermission]


GrafanaUsersWithPermissions = typing.List[GrafanaUserWithPermissions]
UserPermissionsDict = typing.Dict[str, typing.List[GrafanaAPIPermission]]


class GCOMInstanceInfoConfigFeatureToggles(typing.TypedDict):
    accessControlOnCall: typing.NotRequired[str]


class GCOMInstanceInfoConfig(typing.TypedDict):
    feature_toggles: GCOMInstanceInfoConfigFeatureToggles


class GCOMInstanceInfo(typing.TypedDict):
    id: int
    orgId: int
    slug: str
    orgSlug: str
    orgName: str
    url: str
    status: str
    clusterSlug: str
    config: typing.NotRequired[GCOMInstanceInfoConfig]


class ApiClientResponseCallStatus(typing.TypedDict):
    url: str
    connected: bool
    status_code: int
    message: str


_RT = typing.TypeVar("_RT")


class APIClientResponse(typing.Generic[_RT], typing.Tuple[typing.Optional[_RT], ApiClientResponseCallStatus]):
    pass


# can't define this using class syntax because one of the keys contains a dash
# https://docs.python.org/3/library/typing.html#typing.TypedDict:~:text=The%20functional%20syntax%20should%20also%20be%20used%20when%20any%20of%20the%20keys%20are%20not%20valid%20identifiers%2C%20for%20example%20because%20they%20are%20keywords%20or%20contain%20hyphens.%20Example%3A
APIRequestHeaders = typing.TypedDict(
    "APIRequestHeaders",
    {
        "User-Agent": str,
        "Authorization": str,
    },
)


class HttpMethod(typing.Protocol):
    """
    TODO: can probably replace this with something from the requests library?
    https://github.com/psf/requests/blob/main/requests/api.py#L14
    """

    @property
    def __name__(self) -> str:
        ...

    def __call__(self, *args, **kwargs) -> requests.Response:
        ...


class APIClient:
    def __init__(self, api_url: str, api_token: str) -> None:
        self.api_url = api_url
        self.api_token = api_token

    def api_head(self, endpoint: str, body: typing.Optional[typing.Dict] = None, **kwargs) -> APIClientResponse[_RT]:
        return self.call_api(endpoint, requests.head, body, **kwargs)

    def api_get(self, endpoint: str, **kwargs) -> APIClientResponse[_RT]:
        return self.call_api(endpoint, requests.get, **kwargs)

    def api_post(self, endpoint: str, body: typing.Optional[typing.Dict] = None, **kwargs) -> APIClientResponse[_RT]:
        return self.call_api(endpoint, requests.post, body, **kwargs)

    def api_put(self, endpoint: str, body: typing.Optional[typing.Dict] = None, **kwargs) -> APIClientResponse[_RT]:
        return self.call_api(endpoint, requests.put, body, **kwargs)

    def call_api(
        self, endpoint: str, http_method: HttpMethod, body: typing.Optional[typing.Dict] = None, **kwargs
    ) -> APIClientResponse[_RT]:
        request_start = time.perf_counter()
        call_status: ApiClientResponseCallStatus = {
            "url": urljoin(self.api_url, endpoint),
            "connected": False,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "message": "",
        }
        try:
            response = http_method(call_status["url"], json=body, headers=self.request_headers, **kwargs)
            call_status["status_code"] = response.status_code
            response.raise_for_status()

            call_status["connected"] = True
            call_status["message"] = response.reason

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return {}, call_status

            # ex. a HEAD call (self.api_head) would have a response.content of b''
            # and hence calling response.json() throws a json.JSONDecodeError
            return response.json() if response.content else None, call_status
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.Timeout,
            json.JSONDecodeError,
        ) as e:
            logger.warning("Error connecting to api instance " + str(e))
            call_status["message"] = "{0}".format(e)
        finally:
            request_end = time.perf_counter()
            status_code = call_status["status_code"]
            url = call_status["url"]
            seconds = request_end - request_start
            logging.info(
                f"outbound latency={str(seconds)} status={status_code} "
                f"method={http_method.__name__.upper()} url={url} "
                f"slow={int(seconds > settings.SLOW_THRESHOLD_SECONDS)} "
            )
        return None, call_status

    @property
    def request_headers(self) -> APIRequestHeaders:
        return {"User-Agent": settings.GRAFANA_COM_USER_AGENT, "Authorization": f"Bearer {self.api_token}"}


class GrafanaAPIClient(APIClient):
    GRAFANA_INCIDENT_PLUGIN = "grafana-incident-app"
    GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY = "backendUrl"
    GRAFANA_LABELS_PLUGIN = "grafana-labels-app"

    USER_PERMISSION_ENDPOINT = f"api/access-control/users/permissions/search?actionPrefix={ACTION_PREFIX}"

    class Types:
        class _BaseGrafanaAPIResponse(typing.TypedDict):
            totalCount: int
            page: int
            perPage: int

        class GrafanaTeam(typing.TypedDict):
            id: int
            orgId: int
            name: str
            email: str
            avatarUrl: str
            memberCount: int

        class GrafanaServiceAccount(typing.TypedDict):
            id: int
            name: str
            login: str
            orgId: int
            isDisabled: bool
            role: str
            tokens: int
            avatarUrl: str

        class GrafanaServiceAccountToken(typing.TypedDict):
            id: int
            name: str
            key: str

        class PluginSettings(typing.TypedDict):
            enabled: bool
            jsonData: typing.NotRequired[typing.Dict[str, str]]

        class TeamsResponse(_BaseGrafanaAPIResponse):
            teams: typing.List["GrafanaAPIClient.Types.GrafanaTeam"]

        class ServiceAccountResponse(_BaseGrafanaAPIResponse):
            serviceAccounts: typing.List["GrafanaAPIClient.Types.GrafanaServiceAccount"]

    def __init__(self, api_url: str, api_token: str) -> None:
        super().__init__(api_url, api_token)

    def check_token(self) -> APIClientResponse:
        return self.api_head("api/org")

    def get_users_permissions(self) -> typing.Optional[UserPermissionsDict]:
        """
        It is possible that this endpoint may not be available for certain Grafana orgs.
        Ex: for Grafana Cloud orgs whom have pinned their Grafana version to an earlier version
        where this endpoint is not available

        The response from the Grafana endpoint will look something like this:
        {
            "1": {
                "grafana-oncall-app.alert-groups:read": [
                    ""
                ],
                "grafana-oncall-app.alert-groups:write": [
                    ""
                ]
            }
        }
        """
        response, _ = self.api_get(self.USER_PERMISSION_ENDPOINT)
        if response is None or isinstance(response, list):
            return None

        data: typing.Dict[str, typing.Dict[str, typing.List[str]]] = response

        all_users_permissions: UserPermissionsDict = {}
        for user_id, user_permissions in data.items():
            all_users_permissions[user_id] = [GrafanaAPIPermission(action=key) for key, _ in user_permissions.items()]

        return all_users_permissions

    def is_rbac_enabled_for_organization(self) -> bool:
        _, resp_status = self.api_head(self.USER_PERMISSION_ENDPOINT)
        return resp_status["connected"]

    def get_users(self, rbac_is_enabled_for_org: bool, **kwargs) -> GrafanaUsersWithPermissions:
        users_response, _ = self.api_get("api/org/users", **kwargs)

        if not users_response:
            return []
        elif isinstance(users_response, dict):
            return []

        users: GrafanaUsersWithPermissions = users_response

        user_permissions = {}
        if rbac_is_enabled_for_org:
            user_permissions = self.get_users_permissions()
            if user_permissions is None:
                # If we cannot fetch permissions when RBAC is enabled (ex. HTTP 500), we should not return any users
                # to avoid potentially wiping-out OnCall's copy of permissions for all users
                return []

        # merge the users permissions response into the org users response
        for user in users:
            user["permissions"] = user_permissions.get(str(user["userId"]), [])
        return users

    def get_teams(self, **kwargs) -> APIClientResponse["GrafanaAPIClient.Types.TeamsResponse"]:
        """
        [Grafana API Docs](https://grafana.com/docs/grafana/latest/developers/http_api/team/#team-search-with-paging)
        """
        return self.api_get("api/teams/search?perpage=1000000", **kwargs)

    def get_team_members(self, team_id: int) -> APIClientResponse:
        return self.api_get(f"api/teams/{team_id}/members")

    def get_datasources(self) -> APIClientResponse:
        return self.api_get("api/datasources")

    def get_datasource_by_id(self, datasource_id) -> APIClientResponse:
        # This endpoint is deprecated for Grafana version >= 9. Use get_datasource instead
        return self.api_get(f"api/datasources/{datasource_id}")

    def get_datasource(self, datasource_uid) -> APIClientResponse:
        return self.api_get(f"api/datasources/uid/{datasource_uid}")

    def get_alertmanager_status_with_config(self, recipient) -> APIClientResponse:
        return self.api_get(f"api/alertmanager/{recipient}/api/v2/status")

    def get_alerting_config(self, recipient: str) -> APIClientResponse:
        return self.api_get(f"api/alertmanager/{recipient}/config/api/v1/alerts")

    def update_alerting_config(self, recipient, config) -> APIClientResponse:
        return self.api_post(f"api/alertmanager/{recipient}/config/api/v1/alerts", config)

    def get_alerting_notifiers(self):
        return self.api_get("api/alert-notifiers")

    def get_grafana_plugin_settings(self, recipient: str) -> APIClientResponse["GrafanaAPIClient.Types.PluginSettings"]:
        return self.api_get(f"api/plugins/{recipient}/settings")

    def get_grafana_incident_plugin_settings(self) -> APIClientResponse["GrafanaAPIClient.Types.PluginSettings"]:
        return self.get_grafana_plugin_settings(self.GRAFANA_INCIDENT_PLUGIN)

    def get_grafana_labels_plugin_settings(self) -> APIClientResponse["GrafanaAPIClient.Types.PluginSettings"]:
        return self.get_grafana_plugin_settings(self.GRAFANA_LABELS_PLUGIN)

    def get_service_account(self, login: str) -> APIClientResponse["GrafanaAPIClient.Types.ServiceAccountResponse"]:
        return self.api_get(f"api/serviceaccounts/search?query={login}")

    def create_service_account(
        self, name: str, role: str
    ) -> APIClientResponse["GrafanaAPIClient.Types.GrafanaServiceAccount"]:
        return self.api_post("api/serviceaccounts", {"name": name, "role": role})

    def create_service_account_token(
        self, service_account_id: int, name: str, seconds_to_live=int | None
    ) -> APIClientResponse["GrafanaAPIClient.Types.GrafanaServiceAccountToken"]:
        token_config = {"name": name}
        if seconds_to_live:
            token_config["secondsToLive"] = seconds_to_live
        return self.api_post(f"api/serviceaccounts/{service_account_id}/tokens", token_config)

    def get_service_account_token_permissions(self) -> APIClientResponse[typing.Dict[str, typing.List[str]]]:
        return self.api_get("api/access-control/user/permissions")


class GcomAPIClient(APIClient):
    ACTIVE_INSTANCE_QUERY = "instances?status=active"
    DELETED_INSTANCE_QUERY = "instances?status=deleted&includeDeleted=true"
    STACK_STATUS_DELETED = "deleted"
    STACK_STATUS_ACTIVE = "active"
    PAGE_SIZE = 1000

    def __init__(self, api_token: str) -> None:
        super().__init__(settings.GRAFANA_COM_API_URL, api_token)

    def get_instance_info(
        self, stack_id: str, include_config_query_param: bool = False
    ) -> typing.Optional[GCOMInstanceInfo]:
        """
        NOTE: in order to use ?config=true, an "Admin" GCOM token must be used to make the API call
        """
        url = f"instances/{stack_id}"
        if include_config_query_param:
            url += "?config=true"

        data, _ = self.api_get(url)
        return data

    def get_instances(self, query: str, page_size=None):
        if not page_size:
            page, _ = self.api_get(query)
            yield page
        else:
            cursor = 0
            while cursor is not None:
                if query:
                    page_query = query + f"&cursor={cursor}&pageSize={page_size}"
                else:
                    page_query = f"?cursor={cursor}&pageSize={page_size}"
                page, _ = self.api_get(page_query)
                yield page
                cursor = page["nextCursor"]

    def _is_stack_in_certain_state(self, stack_id: str, state: str) -> bool:
        instance_info = self.get_instance_info(stack_id)
        if not instance_info:
            return False
        return instance_info.get("status") == state

    def is_stack_deleted(self, stack_id: str) -> bool:
        url = f"instances?includeDeleted=true&id={stack_id}"
        instance_infos, _ = self.api_get(url)
        return instance_infos["items"] and instance_infos["items"][0].get("status") == self.STACK_STATUS_DELETED

    def is_stack_active(self, stack_id: str) -> bool:
        return self._is_stack_in_certain_state(stack_id, self.STACK_STATUS_ACTIVE)

    def post_active_users(self, body) -> APIClientResponse:
        return self.api_post("app-active-users", body)

    def get_stack_regions(self) -> APIClientResponse:
        return self.api_get("stack-regions")
