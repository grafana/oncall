import json
import logging
import time
from typing import Optional, Tuple
from urllib.parse import urljoin

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token

    def api_get(self, endpoint: str) -> Tuple[Optional[Response], dict]:
        return self.call_api(endpoint, requests.get)

    def api_post(self, endpoint: str, body: dict = None) -> Tuple[Optional[Response], dict]:
        return self.call_api(endpoint, requests.post, body)

    def call_api(self, endpoint: str, http_method, body: dict = None) -> Tuple[Optional[Response], dict]:
        request_start = time.perf_counter()
        call_status = {
            "url": urljoin(self.api_url, endpoint),
            "connected": False,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "message": "",
        }
        try:
            response = http_method(call_status["url"], json=body, headers=self.request_headers)
            call_status["status_code"] = response.status_code
            response.raise_for_status()

            call_status["connected"] = True
            call_status["message"] = response.reason

            if response.status_code == status.HTTP_204_NO_CONTENT:
                return {}, call_status

            return response.json(), call_status
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.TooManyRedirects,
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
    def request_headers(self) -> dict:
        return {"User-Agent": settings.GRAFANA_COM_USER_AGENT, "Authorization": f"Bearer {self.api_token}"}


class GrafanaAPIClient(APIClient):
    def __init__(self, api_url: str, api_token: str):
        super().__init__(api_url, api_token)

    def check_token(self) -> Tuple[Optional[Response], dict]:
        return self.api_get("api/org")

    def get_users(self) -> Tuple[Optional[Response], dict]:
        """
        Response example:
        [
            {
                'orgId': 1,
                'userId': 1,
                'email': 'user@example.com',
                'name': 'User User',
                'avatarUrl': '/avatar/79163f696e9e08958c0d3f73c160e2cc',
                'login': 'user',
                'role': 'Admin',
                'lastSeenAt': '2021-06-21T07:01:45Z',
                'lastSeenAtAge': '9m'
            },
        ]
        """
        return self.api_get("api/org/users")

    def get_teams(self):
        return self.api_get("api/teams/search?perpage=1000000")

    def get_team_members(self, team_id):
        return self.api_get(f"api/teams/{team_id}/members")

    def get_datasources(self):
        return self.api_get("api/datasources")

    def get_datasource(self, datasource_id):
        return self.api_get(f"api/datasources/{datasource_id}")

    def get_alertmanager_status_with_config(self, recipient):
        return self.api_get(f"api/alertmanager/{recipient}/api/v2/status")

    def get_alerting_config(self, recipient):
        return self.api_get(f"api/alertmanager/{recipient}/config/api/v1/alerts")

    def update_alerting_config(self, config, recipient):
        return self.api_post(f"api/alertmanager/{recipient}/config/api/v1/alerts", config)


class GcomAPIClient(APIClient):
    STACK_STATUS_DELETED = "deleted"

    def __init__(self, api_token: str):
        super().__init__(settings.GRAFANA_COM_API_URL, api_token)

    def check_token(self):
        return self.api_post("api-keys/check", {"token": self.api_token})

    def get_instance_info(self, stack_id: str):
        return self.api_get(f"instances/{stack_id}")

    def get_active_instances(self):
        return self.api_get("instances?status=active")

    def is_stack_deleted(self, stack_id: str) -> bool:
        instance_info, call_status = self.get_instance_info(stack_id)
        return instance_info and instance_info.get("status") == self.STACK_STATUS_DELETED

    def post_active_users(self, body):
        return self.api_post("app-active-users", body)
