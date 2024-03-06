import typing

import pytest
from rest_framework import status
from slack_sdk.web import SlackResponse


def build_slack_response(
    data: dict[str, typing.Any],
    status_code: int = status.HTTP_200_OK,
    headers: typing.Optional[dict[str, typing.Any]] = None,
):
    return SlackResponse(
        client=None,
        http_verb="POST",
        api_url="test",
        req_args={},
        data=data,
        headers=headers if headers else {},
        status_code=status_code,
    )


@pytest.fixture
def get_slack_team_and_slack_user(make_organization_and_user_with_slack_identities):
    def _make_slack_team_and_slack_user(organization, user):
        slack_team_identity = organization.slack_team_identity
        slack_user_identity = user.slack_user_identity

        return slack_team_identity, slack_user_identity

    return _make_slack_team_and_slack_user
