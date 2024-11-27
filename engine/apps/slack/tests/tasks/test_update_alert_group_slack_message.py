from unittest.mock import patch

import pytest

from apps.slack.errors import (
    SlackAPICantUpdateMessageError,
    SlackAPIChannelInactiveError,
    SlackAPIChannelNotFoundError,
    SlackAPIMessageNotFoundError,
    SlackAPIRatelimitError,
    SlackAPITokenError,
)
from apps.slack.tasks import update_alert_group_slack_message
from apps.slack.tests.conftest import build_slack_response


@pytest.fixture
def mocked_rate_limited_slack_response():
    return build_slack_response({}, status_code=429, headers={"Retry-After": 123})


class TestUpdateAlertGroupSlackMessageTask:
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_slack_message_not_found(self):
        """
        Test that the task exits early if SlackMessage does not exist.
        """
        # No need to patch anything, just run the task with a non-existing pk
        update_alert_group_slack_message.apply((99999,), task_id="task-id")

        # Since there is no exception raised, the test passes

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_task_id_mismatch(
        self,
        mock_chat_update,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
    ):
        """
        Test that the task exits early if current_task_id doesn't match active_update_task_id.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="original-task-id"
        )

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="different-task-id")

        # Ensure that SlackClient.chat_update is not called
        mock_chat_update.assert_not_called()

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_no_alert_group(
        self,
        mock_chat_update,
        make_organization_with_slack_team_identity,
        make_slack_channel,
        make_slack_message,
    ):
        """
        Test that the task exits early if SlackMessage has no alert_group.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=None, channel=slack_channel, organization=organization, active_update_task_id="task-id"
        )

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Ensure that SlackClient.chat_update is not called
        mock_chat_update.assert_not_called()

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_successful(
        self,
        mock_chat_update,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
    ):
        """
        Test that the task successfully updates the alert group's Slack message.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="task-id"
        )

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Assert that SlackClient.chat_update was called with correct parameters
        mock_chat_update.assert_called_once_with(
            channel=slack_message._channel_id,
            ts=slack_message.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        # Verify that active_update_task_id is cleared and last_updated is set
        slack_message.refresh_from_db()
        assert slack_message.active_update_task_id is None
        assert slack_message.last_updated is not None

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_ratelimit_error_not_maintenance(
        self,
        mock_start_send_rate_limit_message_task,
        mock_chat_update,
        mocked_rate_limited_slack_response,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
    ):
        """
        Test handling of SlackAPIRatelimitError when not a maintenance integration.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)

        # Ensure channel is not a maintenance integration and not already rate-limited
        assert alert_receive_channel.is_maintenace_integration is False
        assert alert_receive_channel.is_rate_limited_in_slack is False

        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="task-id"
        )

        # SlackClient.chat_update raises SlackAPIRatelimitError
        slack_api_ratelimit_error = SlackAPIRatelimitError(mocked_rate_limited_slack_response)
        mock_chat_update.side_effect = slack_api_ratelimit_error

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Assert that start_send_rate_limit_message_task was called
        mock_start_send_rate_limit_message_task.assert_called_with("Updating", slack_api_ratelimit_error.retry_after)

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_ratelimit_error_is_maintenance(
        self,
        mock_start_send_rate_limit_message_task,
        mock_chat_update,
        mocked_rate_limited_slack_response,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
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

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="task-id"
        )

        # SlackClient.chat_update raises SlackAPIRatelimitError
        slack_api_ratelimit_error = SlackAPIRatelimitError(mocked_rate_limited_slack_response)
        mock_chat_update.side_effect = slack_api_ratelimit_error

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Assert that start_send_rate_limit_message_task was not called, and task id is not cleared
        mock_start_send_rate_limit_message_task.assert_not_called()
        assert slack_message.active_update_task_id == "task-id"

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.parametrize(
        "ExceptionClass",
        [
            SlackAPIMessageNotFoundError,
            SlackAPICantUpdateMessageError,
            SlackAPIChannelInactiveError,
            SlackAPITokenError,
            SlackAPIChannelNotFoundError,
        ],
    )
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_other_exceptions(
        self,
        mock_start_send_rate_limit_message_task,
        mock_chat_update,
        ExceptionClass,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
    ):
        """
        Test that other Slack API exceptions are handled silently.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="task-id"
        )

        # SlackClient.chat_update raises the exception class
        mock_chat_update.side_effect = ExceptionClass("foo bar")

        # Call the task
        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Ensure that exception was caught and passed
        # SlackClient.chat_update was called
        mock_chat_update.assert_called_once()

        # Assert that start_send_rate_limit_message_task was not called
        mock_start_send_rate_limit_message_task.assert_not_called()

        # Verify that active_update_task_id is cleared and last_updated is set
        slack_message.refresh_from_db()
        assert slack_message.active_update_task_id is None
        assert slack_message.last_updated is not None

    @patch("apps.slack.tasks.SlackClient.chat_update")
    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_unexpected_exception(
        self,
        mock_start_send_rate_limit_message_task,
        mock_chat_update,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_channel,
        make_slack_message,
        make_alert_group,
        make_alert,
    ):
        """
        Test that an unexpected exception propagates as expected.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data={})

        slack_channel = make_slack_channel(slack_team_identity)
        slack_message = make_slack_message(
            alert_group=alert_group, channel=slack_channel, active_update_task_id="task-id"
        )

        # SlackClient.chat_update raises a generic exception
        mock_chat_update.side_effect = ValueError("Unexpected error")

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Assert that start_send_rate_limit_message_task was not called, and task id is not cleared
        mock_start_send_rate_limit_message_task.assert_not_called()
        assert slack_message.active_update_task_id == "task-id"
