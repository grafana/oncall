import typing
from urllib.parse import parse_qs, urlparse

from lib.network import api_call
from lib.opsgenie.config import OPSGENIE_API_KEY, OPSGENIE_API_URL


class OpsGenieAPIClient:
    DEFAULT_LIMIT = 100  # Maximum allowed by OpsGenie API

    def __init__(
        self, api_key: str = OPSGENIE_API_KEY, api_url: str = OPSGENIE_API_URL
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": f"GenieKey {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        path: str,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
        paginate: bool = True,
    ) -> dict:
        """
        Make a request to the OpsGenie API with automatic pagination handling.
        If paginate=True and method is GET, it will automatically handle pagination
        and combine all results into a single response.

        NOTE: we need to be careful with rate limiting, this is handled inside of lib.network.api_call
        (see HTTP 429 exception handling)
        # https://docs.opsgenie.com/docs/api-rate-limiting
        """
        if params is None:
            params = {}

        # Only handle pagination for GET requests when pagination is requested
        if method.upper() != "GET" or not paginate:
            response = api_call(
                method,
                self.api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            return response.json()

        # Set default pagination parameters
        if "limit" not in params:
            params["limit"] = self.DEFAULT_LIMIT
        if "offset" not in params:
            params["offset"] = 0

        # Initialize combined response
        combined_response = None

        while True:
            response = api_call(
                method,
                self.api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            response_json = response.json()

            if combined_response is None:
                combined_response = response_json
            else:
                # Extend the data array with new items
                combined_response["data"].extend(response_json.get("data", []))

            # Check if there's more data to fetch
            data = response_json.get("data", [])
            if not data:
                break

            # Check if there's a next page in the paging information
            paging = response_json.get("paging", {})
            next_url = paging.get("next")
            if not next_url:
                break

            # Parse the next URL to get the new offset
            parsed_url = urlparse(next_url)
            query_params = parse_qs(parsed_url.query)

            try:
                params["offset"] = int(query_params.get("offset", [0])[0])
            except (ValueError, IndexError):
                break

        return combined_response

    def list_users(self) -> list[dict]:
        """List all users with their notification rules."""
        users = []
        response = self._make_request("GET", "v2/users")

        for user in response.get("data", []):
            # Map username to email for compatibility with matching function
            user["email"] = user["username"]

            # Get notification rules for each user
            user_id = user["id"]
            rules_response = self._make_request(
                "GET", f"v2/users/{user_id}/notification-rules"
            )

            # Find the create-alert notification rule
            create_alert_rule = None
            for rule in rules_response.get("data", []):
                if rule.get("actionType") == "create-alert":
                    create_alert_rule = rule
                    break

            if create_alert_rule:
                # Get steps for the create-alert rule
                steps_response = self._make_request(
                    "GET",
                    f"v2/users/{user_id}/notification-rules/{create_alert_rule['id']}/steps",
                )
                user["notification_rules"] = steps_response.get("data", [])
            else:
                user["notification_rules"] = []

            # Get teams for each user
            teams_response = self._make_request("GET", f"v2/users/{user_id}/teams")
            user["teams"] = teams_response.get("data", [])

            users.append(user)

        return users

    def list_schedules(self) -> list[dict]:
        """List all schedules with their rotations."""
        response = self._make_request(
            "GET", "v2/schedules", params={"expand": "rotation"}
        )
        schedules = response.get("data", [])

        # Fetch overrides for each schedule
        for schedule in schedules:
            overrides_response = self._make_request(
                "GET", f"v2/schedules/{schedule['id']}/overrides"
            )
            schedule["overrides"] = overrides_response.get("data", [])

        return schedules

    def list_escalation_policies(self) -> list[dict]:
        """List all escalation policies."""
        response = self._make_request("GET", "v2/escalations")
        return response.get("data", [])

    def list_teams(self) -> list[dict]:
        """List all teams."""
        response = self._make_request("GET", "v2/teams")
        return response.get("data", [])

    def list_integrations(self) -> list[dict]:
        """List all integrations."""
        response = self._make_request("GET", "v2/integrations")
        return response.get("data", [])

    def list_services(self) -> list[dict]:
        """List all services."""
        response = self._make_request("GET", "services")
        return response.get("data", [])
