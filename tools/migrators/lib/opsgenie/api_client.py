import typing

from lib.network import api_call
from lib.opsgenie.config import OPSGENIE_API_KEY, OPSGENIE_API_URL


class OpsGenieAPIClient:
    def __init__(self, api_key: str = OPSGENIE_API_KEY, api_url: str = OPSGENIE_API_URL):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"GenieKey {api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        path: str,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
    ) -> dict:
        return api_call(method, self.api_url, path, headers=self.headers, params=params, json=json)

    def list_users(self) -> list[dict]:
        """List all users with their notification rules."""
        users = []
        params = {"limit": 100, "offset": 0}

        while True:
            response = self._make_request("GET", "users", params=params)
            data = response.get("data", [])
            if not data:
                break

            for user in data:
                # Get notification rules for each user
                user_id = user["id"]
                rules_response = self._make_request(
                    "GET", f"users/{user_id}/notification-rules"
                )
                user["notification_rules"] = rules_response.get("data", [])
                users.append(user)

            params["offset"] += params["limit"]

        return users

    def list_schedules(self) -> list[dict]:
        """List all schedules with their rotations."""
        response = self._make_request("GET", "schedules", params={"expand": "rotation"})
        return response.get("data", [])

    def list_escalation_policies(self) -> list[dict]:
        """List all escalation policies."""
        response = self._make_request("GET", "escalation-policies")
        return response.get("data", [])

    def list_teams(self) -> list[dict]:
        """List all teams."""
        response = self._make_request("GET", "teams")
        return response.get("data", [])

    def list_integrations(self) -> list[dict]:
        """List all integrations."""
        response = self._make_request("GET", "integrations")
        return response.get("data", [])

    def list_services(self) -> list[dict]:
        """List all services."""
        response = self._make_request("GET", "services")
        return response.get("data", [])
