from dataclasses import dataclass
from typing import Optional

import requests
from requests.auth import AuthBase
from requests.models import PreparedRequest

from apps.base.utils import live_settings
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid


class TokenAuth(AuthBase):
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


@dataclass
class MattermostChannel:
    channel_id: str
    team_id: str
    channel_name: str
    display_name: str


class MattermostClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or live_settings.MATTERMOST_BOT_TOKEN
        self.base_url = f"{live_settings.MATTERMOST_HOST}/api/v4"
        self.timeout: int = 10

        if self.token is None:
            raise MattermostAPITokenInvalid

    def _check_response(self, response: requests.models.Response):
        try:
            response.raise_for_status()
        except requests.HTTPError as ex:
            raise MattermostAPIException(
                status=ex.response.status_code,
                url=ex.response.request.url,
                msg=ex.response.json()["message"],
                method=ex.response.request.method,
            )
        except requests.Timeout as ex:
            raise MattermostAPIException(
                status=ex.response.status_code,
                url=ex.response.request.url,
                msg="Mattermost api call gateway timedout",
                method=ex.response.request.method,
            )
        except requests.exceptions.RequestException as ex:
            raise MattermostAPIException(
                status=ex.response.status_code,
                url=ex.response.request.url,
                msg="Unexpected error from mattermost server",
                method=ex.response.request.method,
            )

    def get_channel_by_name_and_team_name(self, team_name: str, channel_name: str) -> MattermostChannel:
        url = f"{self.base_url}/teams/name/{team_name}/channels/name/{channel_name}"
        response = requests.get(url=url, timeout=self.timeout, auth=TokenAuth(self.token))
        self._check_response(response)
        data = response.json()
        return MattermostChannel(
            channel_id=data["id"], team_id=data["team_id"], channel_name=data["name"], display_name=data["display_name"]
        )
