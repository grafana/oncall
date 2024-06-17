from dataclasses import dataclass, field
from json import JSONDecodeError
from typing import List
from urllib.parse import urljoin

import requests
from django.conf import settings

SERVICE_TYPE_ONCALL = "oncall"
PROVIDER_TYPE_SLACK = "slack"


@dataclass
class SlackLink:
    service_type: str
    service_tenant_id: str
    slack_team_id: str


@dataclass
class MSTeamsLink:
    service_type: str
    service_tenant_id: str
    msteams_id: str


@dataclass
class Tenant:
    service_tenant_id: str
    service_type: str
    cluster_slug: str
    slack_links: List[SlackLink] = field(default_factory=list)
    msteams_links: List[MSTeamsLink] = field(default_factory=list)


@dataclass
class OAuthInstallation:
    id: str
    oauth_response: dict
    stack_id: int
    provider_type: str
    provider_id: str


class ChatopsProxyAPIException(Exception):
    """A generic 400 or 500 level exception from the Chatops Proxy API"""

    def __init__(self, status, url, msg="", method="GET"):
        self.url = url
        self.status = status
        self.method = method

        # Error-message returned by chatops-proxy.
        # Since chatops-proxy is internal service messages shouldn't be exposed to the user
        self.msg = msg

    def __str__(self):
        return f"ChatopsProxyAPIException: status={self.status} url={self.url} method={self.method} error={self.msg}"


class ChatopsProxyAPIClient:
    def __init__(self, url: str, token: str):
        self.api_base_url = urljoin(url, "api/v3")
        self.api_token = token

    # OnCall Tenant
    def register_tenant(
        self, service_tenant_id: str, cluster_slug: str, service_type: str, stack_id: int
    ) -> tuple[Tenant, requests.models.Response]:
        url = f"{self.api_base_url}/tenants/register"
        d = {
            "tenant": {
                "service_tenant_id": service_tenant_id,
                "cluster_slug": cluster_slug,
                "service_type": service_type,
                "stack_id": stack_id,
            }
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)

        return Tenant(**response.json()["tenant"]), response

    def unregister_tenant(
        self, service_tenant_id: str, cluster_slug: str, service_type: str
    ) -> tuple[bool, requests.models.Response]:
        url = f"{self.api_base_url}/tenants/unregister"
        d = {
            "tenant": {
                "service_tenant_id": service_tenant_id,
                "cluster_slug": cluster_slug,
                "service_type": service_type,
            }
        }

        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)

        return response.json()["removed"], response

    def can_slack_link(
        self, service_tenant_id: str, cluster_slug: str, slack_team_id: str, service_type: str
    ) -> requests.models.Response:
        url = f"{self.api_base_url}/providers/slack/can_link"
        d = {
            "service_type": service_type,
            "service_tenant_id": service_tenant_id,
            "cluster_slug": cluster_slug,
            "slack_team_id": slack_team_id,
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)
        return response

    def link_slack_team(
        self, service_tenant_id: str, slack_team_id: str, service_type: str
    ) -> tuple[SlackLink, requests.models.Response]:
        url = f"{self.api_base_url}/providers/slack/link"
        d = {
            "slack_link": {
                "service_type": service_type,
                "service_tenant_id": service_tenant_id,
                "slack_team_id": slack_team_id,
            }
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)
        return SlackLink(**response.json()["slack_link"]), response

    def unlink_slack_team(
        self, service_tenant_id: str, slack_team_id: str, service_type: str
    ) -> tuple[bool, requests.models.Response]:
        url = f"{self.api_base_url}/providers/slack/unlink"
        d = {
            "slack_link": {
                "service_type": service_type,
                "service_tenant_id": service_tenant_id,
                "slack_team_id": slack_team_id,
            }
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)
        return response.json()["removed"], response

    def get_slack_oauth_link(
        self, stack_id: int, grafana_user_id: int, app_redirect: str, app_type: str
    ) -> tuple[str, requests.models.Response]:
        url = f"{self.api_base_url}/oauth2/start"
        d = {
            "stack_id": stack_id,
            "grafana_user_id": grafana_user_id,
            "app_redirect": app_redirect,
            "app_type": app_type,
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)
        return response.json()["install_link"], response

    def get_oauth_installation(
        self,
        stack_id: int,
        provider_type: str,
    ) -> tuple[OAuthInstallation, requests.models.Response]:
        url = f"{self.api_base_url}/oauth_installations/get"
        d = {
            "stack_id": stack_id,
            "provider_type": provider_type,
        }
        response = requests.post(url=url, json=d, headers=self._headers)
        self._check_response(response)
        return OAuthInstallation(**response.json()["oauth_installation"]), response

    def _check_response(self, response: requests.models.Response):
        """
        Wraps an exceptional response to ChatopsProxyAPIException
        """
        message = None

        if 400 <= response.status_code < 500:
            try:
                error_data = response.json()
                message = error_data.get("error", None)
            except JSONDecodeError:
                message = response.reason
        elif 500 <= response.status_code < 600:
            message = response.reason

        if message:
            raise ChatopsProxyAPIException(
                status=response.status_code,
                url=response.request.url,
                msg=message,
                method=response.request.method,
            )

    @property
    def _headers(self) -> dict:
        return {
            "User-Agent": settings.GRAFANA_COM_USER_AGENT,
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
