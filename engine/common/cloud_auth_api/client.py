import enum
import json
import typing
from urllib.parse import urljoin

import requests
from django.conf import settings
from rest_framework import status

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class CloudAuthApiException(Exception):
    """A generic 400 or 500 level exception from the Cloud Auth API"""

    def __init__(self, status, url, msg="", method="GET"):
        self.url = url
        self.status = status
        self.method = method
        self.msg = msg

    def __str__(self):
        return f"CloudAuthApiException: status={self.status} url={self.url} method={self.method} error={self.msg}"


class CloudAuthApiClient:
    class Scopes(enum.StrEnum):
        INCIDENT_WRITE = "incident:write"

    def __init__(self):
        if settings.GRAFANA_CLOUD_AUTH_API_URL is None or settings.GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN is None:
            raise RuntimeError(
                "GRAFANA_CLOUD_AUTH_API_URL and GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN must be set"
                "to use CloudAuthApiClient"
            )

        self.api_base_url = settings.GRAFANA_CLOUD_AUTH_API_URL
        self.api_token = settings.GRAFANA_CLOUD_AUTH_API_SYSTEM_TOKEN

    def request_signed_token(
        self, org: "Organization", scopes: typing.List[Scopes], claims: typing.Dict[str, typing.Any]
    ) -> str:
        org_id = org.org_id
        stack_id = org.stack_id

        # NOTE: header values must always be strings
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            # need to cast to str otherwise - requests.exceptions.InvalidHeader: Header part ... from ('X-Org-ID', 5000)
            # must be of type str or bytes, not <class 'int'>
            "X-Org-ID": str(org_id),
            "X-Realms": json.dumps(
                [
                    {
                        "type": "stack",
                        "identifier": str(stack_id),
                    },
                ]
            ),
        }

        url = urljoin(self.api_base_url, "v1/sign")
        response = requests.post(
            url,
            headers=headers,
            json={
                "claims": claims,
                "extra": {
                    "scopes": scopes,
                    "org_id": org_id,
                },
            },
        )

        if response.status_code != status.HTTP_200_OK:
            raise CloudAuthApiException(response.status_code, url, response.text, method="POST")
        return response.json()["data"]["token"]
