import secrets
from urllib.parse import urljoin

import requests


class GrafanaAPIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def _api_call(self, method: str, path: str, **kwargs):
        return requests.request(
            method,
            urljoin(self.base_url, path),
            auth=(self.username, self.password),
            **kwargs,
        )

    def create_user_with_random_password(self, name: str, email: str):
        return self._api_call(
            "POST",
            "/api/admin/users",
            json={
                "name": name,
                "email": email,
                "login": email.split("@")[0],
                "password": secrets.token_urlsafe(15),
            },
        )

    def get_all_users(self):
        """
        https://grafana.com/docs/grafana/v10.3/developers/http_api/user/#search-users
        """
        return self._api_call("GET", "/api/users").json()

    def idemopotently_create_team_and_add_users(
        self, team_name: str, user_emails: list[str]
    ) -> int:
        """
        Get team by name
        https://grafana.com/docs/grafana/v10.3/developers/http_api/team/#using-the-name-parameter


        Create team
        https://grafana.com/docs/grafana/v10.3/developers/http_api/team/#add-team

        Add team members
        https://grafana.com/docs/grafana/v10.3/developers/http_api/team/#add-team-member
        """
        existing_team = self._api_call(
            "GET", "/api/teams/search", params={"name": team_name}
        ).json()

        if existing_team["teams"]:
            # team already exists
            team_id = existing_team["teams"][0]["id"]
        else:
            # team doesn't exist create it
            response = self._api_call("POST", "/api/teams", json={"name": team_name})

            if response.status_code == 200:
                team_id = response.json()["teamId"]
            else:
                raise Exception(f"Failed to fetch/create Grafana team '{team_name}'")

        grafana_users = self.get_all_users()
        grafana_user_id_to_email_map = {}

        for user_email in user_emails:
            for grafana_user in grafana_users:
                if grafana_user["email"] == user_email:
                    grafana_user_id_to_email_map[grafana_user["id"]] = user_email
                    break

        for user_id in grafana_user_id_to_email_map.keys():
            self._api_call(
                "POST", f"/api/teams/{team_id}/members", json={"userId": user_id}
            )

        return team_id
