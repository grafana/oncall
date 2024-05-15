import time
import typing

from lib.network import api_call as _api_call
from lib.splunk import types


class SplunkOnCallAPIClient:
    """
    https://portal.victorops.com/public/api-docs.html
    """

    PUBLIC_API_BASE_URL = "https://api.victorops.com/api-public/"

    def __init__(self, api_id: str, api_key: str):
        self.api_id = api_id
        self.api_key = api_key

    def _api_call(
        self,
        method: str,
        path: str,
        response_key: typing.Optional[str] = None,
        **kwargs,
    ):
        """
        According to the docs, most API endpoints may only be called a maximum of 2 times per second
        (hence the built-in `time.sleep`)
        """
        time.sleep(0.5)

        response = _api_call(
            method,
            self.PUBLIC_API_BASE_URL,
            path,
            headers={
                "X-VO-Api-Id": self.api_id,
                "X-VO-Api-Key": self.api_key,
            },
            **kwargs,
        )

        return response.json()[response_key] if response_key else response.json()

    def fetch_user_paging_policies(
        self, user_id: str
    ) -> typing.List[types.SplunkUserPagingPolicy]:
        """
        https://portal.victorops.com/public/api-docs.html#!/User32Paging32Policies/get_api_public_v1_user_user_policies
        """
        return self._api_call("GET", f"v1/user/{user_id}/policies", "policies")

    def fetch_users(
        self, include_paging_policies=True
    ) -> typing.List[types.SplunkUserWithPagingPolicies]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Users/get_api_public_v2_user
        """
        users: typing.List[types.SplunkUserWithPagingPolicies] = self._api_call(
            "GET", "v2/user", "users"
        )

        if include_paging_policies:
            for user in users:
                user["pagingPolicies"] = self.fetch_user_paging_policies(
                    user["username"]
                )

        return users

    def fetch_team_members(self, team_slug: str) -> typing.List[types.SplunkTeamMember]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Teams/get_api_public_v1_team_team_members
        """
        return self._api_call("GET", f"v1/team/{team_slug}/members", "members")

    def fetch_teams(self, include_members=False) -> typing.List[types.SplunkTeam]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Teams/get_api_public_v1_team
        """
        teams = self._api_call("GET", "v1/team")

        if include_members:
            for team in teams:
                team["members"] = self.fetch_team_members(team["slug"])

        return teams

    def fetch_rotations(self, team_slug: str) -> typing.List[types.SplunkRotation]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Rotations/get_api_public_v2_team_team_rotations
        """
        return self._api_call("GET", f"v2/team/{team_slug}/rotations", "rotations")

    def fetch_schedules(self) -> typing.List[types.SplunkScheduleWithTeamAndRotations]:
        """
        Schedules in Splunk must be fetched via a team, there is no
        way to list all schedules

        https://portal.victorops.com/public/api-docs.html#!/On45call/get_api_public_v2_team_team_oncall_schedule
        """
        schedules: typing.List[types.SplunkScheduleWithTeamAndRotations] = []
        for team in self.fetch_teams():
            team_slug = team["slug"]
            team_rotations = self.fetch_rotations(team_slug)

            for team_schedule in self._api_call(
                "GET", f"v2/team/{team_slug}/oncall/schedule", "schedules"
            ):
                team_schedule["team"] = team
                team_schedule["rotations"] = team_rotations

                schedules.append(team_schedule)
        return schedules

    def fetch_escalation_policy(self, policy_id: str) -> types.SplunkEscalationPolicy:
        """
        Fetch more detailed info about a specific escalation policy
        https://portal.victorops.com/public/api-docs.html#!/Escalation32Policies/get_api_public_v1_policies_policy
        """
        return self._api_call("GET", f"v1/policies/{policy_id}")

    def fetch_escalation_policies(self) -> typing.List[types.SplunkEscalationPolicy]:
        """
        https://portal.victorops.com/public/api-docs.html#!/Escalation32Policies/get_api_public_v1_policies
        """
        return [
            self.fetch_escalation_policy(policy["policy"]["slug"])
            for policy in self._api_call("GET", "v1/policies", "policies")
        ]
