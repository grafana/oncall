import json
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from django.conf import settings


@dataclass
class OnCallConnector:
    """
    OnCallConnector represents connection between oncall org and oncall-gateway
    """

    oncall_org_id: str
    backend: str


@dataclass
class SlackConnector:
    """
    SlackConnector represents connection between slack team with installed oncall app and oncall-gateway
    """

    oncall_org_id: str
    slack_team_id: str
    backend: str


DEFAULT_TIMEOUT = 5


class OnCallGatewayAPIClient:
    def __init__(self, url: str, token: str):
        self.base_url = url
        self.api_base_url = urljoin(self.base_url, "api/v1/")
        self.api_token = token

    # OnCall Connector
    @property
    def _oncall_connectors_url(self) -> str:
        return urljoin(self.api_base_url, "oncall_org_connectors")

    def post_oncall_connector(
        self, oncall_org_id: str, backend: str
    ) -> tuple[OnCallConnector, requests.models.Response]:
        d = {"oncall_org_id": oncall_org_id, "backend": backend}
        response = self._post(url=self._oncall_connectors_url, json=d)
        response_data = response.json()

        return OnCallConnector(oncall_org_id=response_data["oncall_org_id"], backend=response_data["backend"]), response

    def delete_oncall_connector(self, oncall_org_id: str) -> requests.models.Response:
        url = urljoin(f"{self._oncall_connectors_url}/", oncall_org_id)
        response = self._delete(url=url)
        return response

    # Slack Connector
    @property
    def _slack_connectors_url(self) -> str:
        return urljoin(self.api_base_url, "slack_team_connectors")

    def post_slack_connector(
        self, oncall_org_id: str, slack_id: str, backend: str
    ) -> tuple[SlackConnector, requests.models.Response]:
        d = {"oncall_org_id": oncall_org_id, "slack_team_id": slack_id, "backend": backend}
        response = self._post(url=self._slack_connectors_url, json=d)
        response_data = response.json()
        return (
            SlackConnector(
                response_data["oncall_org_id"],
                response_data["slack_team_id"],
                response_data["backend"],
            ),
            response,
        )

    def delete_slack_connector(self, oncall_org_id: str) -> requests.models.Response:
        url = urljoin(f"{self._slack_connectors_url}/", oncall_org_id)
        response = self._delete(url=url)
        return response

    def check_slack_installation_possible(self, oncall_org_id, backend, slack_id: str) -> requests.models.Response:
        url = urljoin(f"{self._slack_connectors_url}/", "check_installation_possible")
        url += f"?slack_team_id={slack_id}&oncall_org_id={oncall_org_id}&backend={backend}"
        return self._get(url=url)

    def _get(self, url, params=None, **kwargs) -> requests.models.Response:
        kwargs["params"] = params
        response = self._call_api(method=requests.get, url=url, **kwargs)
        return response

    def _post(self, url, data=None, json=None, **kwargs) -> requests.models.Response:
        kwargs["data"] = data
        kwargs["json"] = json
        response = self._call_api(method=requests.post, url=url, **kwargs)
        return response

    def _delete(self, url, **kwargs) -> requests.models.Response:
        response = self._call_api(method=requests.delete, url=url, **kwargs)
        return response

    def _call_api(self, method, url, **kwargs) -> requests.models.Response:
        kwargs["headers"] = self._headers | kwargs.get("headers", {})
        response = method(url, **kwargs)
        self._check_response(response)
        return response

    @property
    def _headers(self) -> dict:
        return {
            "User-Agent": settings.GRAFANA_COM_USER_AGENT,
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def _check_response(cls, response: requests.models.Response):
        if response.status_code not in [200, 201, 202, 204]:
            err_msg = cls._get_error_msg_from_response(response)
            if 400 <= response.status_code < 500:
                err_msg = "%s Client Error: %s for url: %s" % (response.status_code, err_msg, response.url)
            elif 500 <= response.status_code < 600:
                err_msg = "%s Server Error: %s for url: %s" % (response.status_code, err_msg, response.url)
            raise requests.exceptions.HTTPError(err_msg, response=response)

    @classmethod
    def _get_error_msg_from_response(cls, response: requests.models.Response) -> str:
        error_msg = ""
        try:
            error_msg = response.json()["message"]
        except (json.JSONDecodeError, KeyError):
            error_msg = response.text if response.text else response.reason
        return error_msg
