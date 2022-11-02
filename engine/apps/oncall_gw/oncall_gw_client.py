import json
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from django.conf import settings

DEFAULT_TIMEOUT = 5


@dataclass
class OnCallConnector:
    oncall_org_id: str
    backend: str


@dataclass
class SlackConnector:
    slack_id: str
    backend: str


class OnCallGwAPIClient:
    def __init__(self, url: str, token: str):
        self.base_url = url
        self.api_token = token

    # OnCall Connector
    @property
    def _oncall_connectors_url(self) -> str:
        return urljoin(self.base_url, "oncall_connectors")

    def post_oncall_connector(
        self, oncall_org_id: str, backend: str
    ) -> tuple[OnCallConnector, requests.models.Response]:
        d = {"oncall_org_id": oncall_org_id, "backend": backend}
        response = self._post(url=self._oncall_connectors_url, data=d)
        response_data = response.json()
        return (
            OnCallConnector(
                response_data["oncall_org_id"],
                response_data["backend"],
            ),
            response,
        )

    # Slack Connector
    @property
    def _slack_connectors_url(self) -> str:
        return urljoin(self.base_url, "slack_installations")

    def post_slack_connector(self, slack_id: str, backend: str) -> tuple[SlackConnector, requests.models.Response]:
        d = {"slack_id": slack_id, "backend": backend}
        response = self._post(url=self._slack_connectors_url, data=d)
        response_data = response.json()
        return (
            OnCallConnector(
                response_data["oncall_org_id"],
                response_data["backend"],
            ),
            response,
        )

    def get_slack_connector(self, slack_id: str) -> tuple[SlackConnector, requests.models.Response]:
        url = urljoin(self._slack_connectors_url, slack_id)
        response = self._get(url=url)
        response_data = response.json()
        return (
            SlackConnector(
                response_data["slack_id"],
                response_data["backend"],
            ),
            response,
        )

    def delete_slack_connector(self, slack_id: str) -> requests.models.Response:
        url = urljoin(self._slack_connectors_url, slack_id)
        response = self._delete(url=url)
        return response

    def _get(self, url, params=None, **kwargs) -> requests.models.Response:
        kwargs["params"] = params
        response = self._call_api(method=requests.get, url=url, **kwargs)
        return response

    def _post(self, url, data=None, json=None, **kwargs) -> requests.models.Response:
        kwargs["data"] = data
        kwargs["json"] = json
        response = self._call_api(method=requests.post, url=url, data=data**kwargs)
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
        if response.status not in [200, 201, 202, 204]:
            err_msg = cls._get_error_msg_from_response(response)
            raise requests.exceptions.HTTPError(err_msg, response)

    @classmethod
    def _get_error_msg_from_response(cls, response: requests.models.Response) -> str:
        error_msg = ""
        try:
            error_msg = response.json["message"]
        except json.JSONDecodeError:
            error_msg = response.text if response.text else response.reason
        return error_msg
