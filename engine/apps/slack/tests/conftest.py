import pytest


@pytest.fixture
def get_slack_team_and_slack_user(make_organization_and_user_with_slack_identities):
    def _make_slack_team_and_slack_user(organization, user):
        slack_team_identity = organization.slack_team_identity
        slack_user_identity = user.slack_user_identity

        return slack_team_identity, slack_user_identity

    return _make_slack_team_and_slack_user
