from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.slack.client import SlackClient
from apps.slack.errors import SlackAPIError
from apps.slack.tests.conftest import build_slack_response


@pytest.fixture
def slack_message_setup(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_channel,
    make_slack_message,
):
    def _slack_message_setup(cached_permalink):
        organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
        integration = make_alert_receive_channel(organization)
        alert_group = make_alert_group(integration)
        slack_channel = make_slack_channel(slack_team_identity)

        return make_slack_message(alert_group=alert_group, channel=slack_channel, cached_permalink=cached_permalink)

    return _slack_message_setup


@pytest.mark.django_db
def test_send_slack_notification(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_user_notification_policy,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    # set up notification policy and alert group
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel=slack_channel)

    with patch("apps.slack.client.SlackClient.conversations_members") as mock_members:
        mock_members.return_value = {"members": [slack_user_identity.slack_id]}
        slack_message.send_slack_notification(user, alert_group, notification_policy)

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@pytest.mark.django_db
def test_slack_message_deep_link(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel=slack_channel)

    expected = (
        f"https://slack.com/app_redirect?channel={slack_channel.slack_id}"
        f"&team={slack_team_identity.slack_id}&message={slack_message.slack_id}"
    )
    assert slack_message.deep_link == expected


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink == "test_permalink"
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    side_effect=SlackAPIError(response=build_slack_response({"ok": False, "error": "message_not_found"})),
)
@pytest.mark.django_db
def test_slack_message_permalink_error(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    assert slack_message.permalink is None
    mock_slack_api_call.assert_called_once()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": True, "permalink": "test_permalink"}),
)
@pytest.mark.django_db
def test_slack_message_permalink_cache(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink="cached_permalink")
    assert slack_message.permalink == "cached_permalink"
    mock_slack_api_call.assert_not_called()


@patch.object(
    SlackClient,
    "chat_getPermalink",
    return_value=build_slack_response({"ok": False, "error": "account_inactive"}),
)
@pytest.mark.django_db
def test_slack_message_permalink_token_revoked(mock_slack_api_call, slack_message_setup):
    slack_message = slack_message_setup(cached_permalink=None)
    slack_message.slack_team_identity.detected_token_revoked = timezone.now()
    slack_message.slack_team_identity.save()

    assert slack_message.slack_team_identity is not None
    assert slack_message.permalink is None

    mock_slack_api_call.assert_not_called()
