from unittest.mock import patch, ANY

import pytest

from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.errors import (
    SlackAPICantUpdateMessageError,
    SlackAPIChannelInactiveError,
    SlackAPIChannelNotFoundError,
    SlackAPIMessageNotFoundError,
    SlackAPIRatelimitError,
    SlackAPITokenError,
)


class MockSlackResponse:
    headers = {"Retry-After": 123}


class TestAlertGroupSlackService:

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_successful(
        self,
        mock_slack_client_chat_update,
        mock_cache,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_message,
    ):
        """
        Test that the Slack message is updated successfully when not debounced.
        """
        slack_message_channel_id = "C12345"
        slack_message_slack_id = "1234567890.123456"

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})
        make_slack_message(
            alert_group=alert_group,
            channel_id=slack_message_channel_id,
            slack_id=slack_message_slack_id,
        )

        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache does not have the key
        mock_cache.get.return_value = None

        # Call the method
        service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
        service.update_alert_group_slack_message(alert_group)

        # Assert that the cache was checked
        mock_cache.get.assert_called_once_with(cache_key)

        # Assert that Slack client's chat_update was called with correct parameters
        mock_slack_client_chat_update.assert_called_once_with(
            channel=slack_message_channel_id,
            ts=slack_message_slack_id,
            attachments=ANY,
            blocks=ANY,
        )

        # Assert that the cache key was set
        mock_cache.set.assert_called_once_with(cache_key, True, 30)

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_debounced(
        self,
        mock_slack_client_chat_update,
        mock_cache,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
    ):
        """
        Test that the update is skipped due to debounce interval.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache has the key (debounced)
        mock_cache.get.return_value = True

        # Call the method
        service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
        service.update_alert_group_slack_message(alert_group)

        # Assert that the cache was checked
        mock_cache.get.assert_called_with(cache_key)

        # Assert that Slack client's chat_update was not called
        mock_slack_client_chat_update.assert_not_called()

        # Assert that the cache set method was not called since the method returns early
        mock_cache.set.assert_not_called()

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_ratelimit_error_not_maintenance(
        self,
        mock_start_send_rate_limit_message_task,
        mock_slack_client_chat_update,
        mock_cache,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_message,
    ):
        """
        Test handling of SlackAPIRatelimitError when not a maintenance integration.
        """
        slack_message_channel_id = "C12345"
        slack_message_slack_id = "1234567890.123456"

        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)

        # Ensure channel is not a maintenance integration and not already rate-limited
        assert alert_receive_channel.is_maintenace_integration is False
        assert alert_receive_channel.is_rate_limited_in_slack is False

        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})
        make_slack_message(
            alert_group=alert_group,
            channel_id=slack_message_channel_id,
            slack_id=slack_message_slack_id,
        )

        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache does not have the key
        mock_cache.get.return_value = None

        # Slack client raises SlackAPIRatelimitError
        slack_api_ratelimit_error = SlackAPIRatelimitError(MockSlackResponse())
        mock_slack_client_chat_update.side_effect = slack_api_ratelimit_error

        # Call the method
        service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
        service.update_alert_group_slack_message(alert_group)

        # Assert that start_send_rate_limit_message_task was called
        mock_start_send_rate_limit_message_task.assert_called_with(
            "Updating",
            slack_api_ratelimit_error.retry_after
        )

        # Assert that cache key was set
        mock_cache.set.assert_called_with(cache_key, True, 30)

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_ratelimit_error_is_maintenance(
        self,
        mock_start_send_rate_limit_message_task,
        mock_slack_client_chat_update,
        mock_cache,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_message,
    ):
        """
        Test that SlackAPIRatelimitError is re-raised when it is a maintenance integration.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization, integration="maintenance")

        # Ensure channel is a maintenance integration and not already rate-limited
        assert alert_receive_channel.is_maintenace_integration is True
        assert alert_receive_channel.is_rate_limited_in_slack is False

        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})
        make_slack_message(alert_group=alert_group)

        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache does not have the key
        mock_cache.get.return_value = None

        # Slack client raises SlackAPIRatelimitError
        slack_api_ratelimit_error = SlackAPIRatelimitError(MockSlackResponse())
        mock_slack_client_chat_update.side_effect = slack_api_ratelimit_error

        # Call the method and expect exception to be raised
        with pytest.raises(SlackAPIRatelimitError):
            service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
            service.update_alert_group_slack_message(alert_group)

        # Assert that start_send_rate_limit_message_task was not called
        mock_start_send_rate_limit_message_task.assert_not_called()

        # Assert that cache key was set even when exception occurred
        mock_cache.set.assert_called_with(cache_key, True, 30)

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.parametrize("ExceptionClass", [
        SlackAPIMessageNotFoundError,
        SlackAPICantUpdateMessageError,
        SlackAPIChannelInactiveError,
        SlackAPITokenError,
        SlackAPIChannelNotFoundError,
    ])
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_other_exceptions(
        self,
        mock_start_send_rate_limit_message_task,
        mock_slack_client_chat_update,
        mock_cache,
        ExceptionClass,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_message,
    ):
        """
        Test that other Slack API exceptions are handled silently.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})
        make_slack_message(alert_group=alert_group)

        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache does not have the key
        mock_cache.get.return_value = None

        # Slack client raises the exception class
        mock_slack_client_chat_update.side_effect = ExceptionClass("foo bar")

        try:
            # Call the method
            service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
            service.update_alert_group_slack_message(alert_group)
        except:
            # Assert that no exception was raised
            pytest.fail()

        # Assert that start_send_rate_limit_message_task was not called
        mock_start_send_rate_limit_message_task.assert_not_called()

        # Assert that cache key was set
        mock_cache.set.assert_called_with(cache_key, True, 30)

    @patch("apps.slack.alert_group_slack_service.cache")
    @patch("apps.slack.alert_group_slack_service.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_cache_key_set_on_exception(
        self,
        mock_start_send_rate_limit_message_task,
        mock_slack_client_chat_update,
        mock_cache,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_message,
    ):
        """
        Test that the cache key is set even when an unexpected exception occurs.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})
        make_slack_message(alert_group=alert_group)

        cache_key = f"debounce_update_alert_group_slack_message_{alert_group.pk}"

        # Cache does not have the key
        mock_cache.get.return_value = None

        # Slack client raises a generic exception
        mock_slack_client_chat_update.side_effect = Exception("Unexpected error")

        # Call the method and expect the exception to propagate
        with pytest.raises(Exception):
            service = AlertGroupSlackService(slack_team_identity=slack_team_identity)
            service.update_alert_group_slack_message(alert_group)

        # Assert that start_send_rate_limit_message_task was not called
        mock_start_send_rate_limit_message_task.assert_not_called()

        # Assert that cache key was set even when exception occurred
        mock_cache.set.assert_called_with(cache_key, True, 30)
