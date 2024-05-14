import requests

from lib.base_config import ONCALL_API_TOKEN, ONCALL_API_URL
from lib.network import api_call as _api_call


class OnCallAPIClient:
    @classmethod
    def api_call(cls, method: str, path: str, **kwargs) -> requests.Response:
        return _api_call(
            method,
            ONCALL_API_URL,
            path,
            headers={"Authorization": ONCALL_API_TOKEN},
            **kwargs
        )

    @classmethod
    def list_all(cls, path: str) -> list[dict]:
        response = cls.api_call("get", path)

        data = response.json()
        results = data["results"]

        while data["next"]:
            response = cls.api_call("get", data["next"])

            data = response.json()
            results += data["results"]

        return results

    @classmethod
    def create(cls, path: str, payload: dict) -> dict:
        response = cls.api_call("post", path, json=payload)
        return response.json()

    @classmethod
    def delete(cls, path: str) -> None:
        try:
            cls.api_call("delete", path)
        except requests.exceptions.HTTPError as e:
            # ignore 404s on delete so deleting resources manually while running the script doesn't break it
            if e.response.status_code != 404:
                raise

    @classmethod
    def update(cls, path: str, payload: dict) -> dict:
        response = cls.api_call("put", path, json=payload)
        return response.json()

    @classmethod
    def list_users_with_notification_rules(cls):
        oncall_users = cls.list_all("users")
        oncall_notification_rules = cls.list_all(
            "personal_notification_rules/?important=false"
        )

        for user in oncall_users:
            user["notification_rules"] = [
                rule
                for rule in oncall_notification_rules
                if rule["user_id"] == user["id"]
            ]

        return oncall_users
