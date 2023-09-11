from unittest.mock import patch

import pytest

from apps.slack.client import SlackClientWithErrorHandling
from apps.slack.errors import SlackAPIError
from apps.slack.tests.conftest import build_slack_response


@pytest.fixture
def slack_message_setup(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_slack_message
):
    def _slack_message_setup(cached_permalink):
        (
            organization,
            user,
            slack_team_identity,
            slack_user_identity,
        ) = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)

        return make_slack_message(alert_group, cached_permalink=cached_permalink)

    return _slack_message_setup


@patch.object(
    SlackClientWithErrorHandling,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink == "test_permalink"
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClientWithErrorHandling,
    "chat_getPermalink",
    side_effect=SlackAPIError(response=build_slack_response({"ok": False, "error": "message_not_found"})),
)
@pytest.mark.django_db
def test_slack_message_permalink_error(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink is None
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClientWithErrorHandling,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink_cache(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink="cached_permalink")
    assert slack_message.permalink == "cached_permalink"
    mock_slack_api_call.assert_not_called()
