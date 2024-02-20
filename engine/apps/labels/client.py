import typing
from json import JSONDecodeError
from urllib.parse import urljoin

import requests
from django.conf import settings

if typing.TYPE_CHECKING:
    from apps.labels.types import LabelKey, LabelOption, LabelValue


class LabelUpdateParam(typing.TypedDict):
    name: str


class LabelsRepoAPIException(Exception):
    """A generic 400 or 500 level exception from the Label Repo API"""

    def __init__(self, status, url, msg="", method="GET"):
        self.url = url
        self.status = status
        self.method = method

        # Error-message returned by label repo.
        # If status is 400 level it will contain user-visible error message.
        self.msg = msg

    def __str__(self):
        return f"LabelsRepoAPIException: status={self.status} url={self.url} method={self.method}"


TIMEOUT = 5


class LabelsAPIClient:
    LABELS_API_URL = "/api/plugins/grafana-labels-app/resources/v1/labels/"

    def __init__(self, api_url: str, api_token: str) -> None:
        self.api_token = api_token
        self.api_url = urljoin(api_url, self.LABELS_API_URL)

    def create_label(
        self, label_data: "LabelUpdateParam"
    ) -> typing.Tuple[typing.Optional["LabelOption"], requests.models.Response]:
        url = self.api_url
        response = requests.post(url, json=label_data, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def get_keys(self) -> typing.Tuple[typing.Optional[typing.List["LabelKey"]], requests.models.Response]:
        url = urljoin(self.api_url, "keys")

        response = requests.get(url, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def get_label_by_key_id(
        self, key_id: str
    ) -> typing.Tuple[typing.Optional["LabelOption"], requests.models.Response]:
        url = urljoin(self.api_url, f"id/{key_id}")

        response = requests.get(url, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def get_value(
        self, key_id: str, value_id: str
    ) -> typing.Tuple[typing.Optional["LabelValue"], requests.models.Response]:
        url = urljoin(self.api_url, f"id/{key_id}/values/{value_id}")

        response = requests.get(url, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def add_value(
        self, key_id: str, label_data: "LabelUpdateParam"
    ) -> typing.Tuple[typing.Optional["LabelOption"], requests.models.Response]:
        url = urljoin(self.api_url, f"id/{key_id}/values")

        response = requests.post(url, json=label_data, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def rename_key(
        self, key_id: str, label_data: "LabelUpdateParam"
    ) -> typing.Tuple[typing.Optional["LabelOption"], requests.models.Response]:
        url = urljoin(self.api_url, f"id/{key_id}")

        response = requests.put(url, json=label_data, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def rename_value(
        self, key_id: str, value_id: str, label_data: "LabelUpdateParam"
    ) -> typing.Tuple[typing.Optional["LabelOption"], requests.models.Response]:
        url = urljoin(self.api_url, f"id/{key_id}/values/{value_id}")

        response = requests.put(url, json=label_data, timeout=TIMEOUT, headers=self._request_headers)
        self._check_response(response)
        return response.json(), response

    def _check_response(self, response: requests.models.Response):
        """
        Wraps an exceptional response to LabelsRepoAPIException
        """
        message = None

        if 400 <= response.status_code < 500:
            try:
                error_data = response.json()
                message = error_data.get("error", response.reason)
            except JSONDecodeError:
                message = response.reason
        elif 500 <= response.status_code < 600:
            message = response.reason

        if message:
            raise LabelsRepoAPIException(
                status=response.status_code,
                url=response.request.url,
                msg=message,
                method=response.request.method,
            )

    @property
    def _request_headers(self):
        return {"User-Agent": settings.GRAFANA_COM_USER_AGENT, "Authorization": f"Bearer {self.api_token}"}
