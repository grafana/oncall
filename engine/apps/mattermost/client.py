import json
from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings
from requests.auth import AuthBase
from requests.models import PreparedRequest

from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid


class TokenAuth(AuthBase):
    def __init__(self, token: str) -> None:
        self.token = token

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


@dataclass
class MattermostUser:
    user_id: str
    username: str
    nickname: str


@dataclass
class MattermostChannel:
    channel_id: str
    team_id: str
    channel_name: str
    display_name: str


@dataclass
class MattermostPost:
    post_id: str
    channel_id: str
    user_id: str


class MattermostClient:
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or settings.MATTERMOST_BOT_TOKEN
        self.base_url = f"{settings.MATTERMOST_HOST}/api/v4"
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

    def get_channel_by_id(self, channel_id: str) -> MattermostChannel:
        url = f"{self.base_url}/channels/{channel_id}"
        response = requests.get(url=url, timeout=self.timeout, auth=TokenAuth(self.token))
        self._check_response(response)
        data = response.json()
        return MattermostChannel(
            channel_id=data["id"], team_id=data["team_id"], channel_name=data["name"], display_name=data["display_name"]
        )

    def get_user(self, user_id: str = "me"):
        url = f"{self.base_url}/users/{user_id}"
        response = requests.get(url=url, timeout=self.timeout, auth=TokenAuth(self.token))
        self._check_response(response)
        data = response.json()
        return MattermostUser(user_id=data["id"], username=data["username"], nickname=data["nickname"])

    def create_post(self, channel_id: str, data: dict):
        url = f"{self.base_url}/posts"
        data.update({"channel_id": channel_id})
        response = requests.post(url=url, data=json.dumps(data), timeout=self.timeout, auth=TokenAuth(self.token))
        self._check_response(response)
        data = response.json()
        return MattermostPost(post_id=data["id"], channel_id=data["channel_id"], user_id=data["user_id"])

    def update_post(self, post_id: str, data: dict):
        url = f"{self.base_url}/posts/{post_id}"
        data.update({"id": post_id})
        response = requests.put(url=url, data=json.dumps(data), timeout=self.timeout, auth=TokenAuth(self.token))
        self._check_response(response)
        data = response.json()
        return MattermostPost(post_id=data["id"], channel_id=data["channel_id"], user_id=data["user_id"])
