from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.slack.errors import SlackAPIFetchMembersFailedError, SlackAPIRatelimitError, get_error_class
from apps.slack.models import SlackMessage
from apps.slack.scenarios.distribute_alerts import IncomingAlertStep
from apps.slack.tests.conftest import build_slack_response

SLACK_MESSAGE_TS = "1234567890.123456"
SLACK_POST_MESSAGE_SUCCESS_RESPONSE = {"ts": SLACK_MESSAGE_TS}


class TestIncomingAlertStep:
    @patch("apps.slack.client.SlackClient.chat_postMessage", return_value=SLACK_POST_MESSAGE_SUCCESS_RESPONSE)
    @pytest.mark.django_db
    def test_process_signal_success_first_message(
        self,
        mock_chat_postMessage,
        make_organization_with_slack_team_identity,
        make_slack_channel,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test the success case where process_signal posts the first Slack message for the alert group.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()

        slack_channel = make_slack_channel(slack_team_identity)
        organization.default_slack_channel = slack_channel
        organization.save()

        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel, slack_message_sent=False)
        alert = make_alert(alert_group, raw_request_data={})

        # Ensure slack_message_sent is False initially
        assert not alert_group.slack_message_sent

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        assert alert_group.slack_message_sent is True

        assert alert_group.slack_message is not None
        assert SlackMessage.objects.count() == 1
        assert alert_group.slack_message.slack_id == SLACK_MESSAGE_TS
        assert alert_group.slack_message.channel == slack_channel

        assert alert.delivered is True

    @patch("apps.slack.client.SlackClient.chat_postMessage", return_value=SLACK_POST_MESSAGE_SUCCESS_RESPONSE)
    @pytest.mark.django_db
    def test_incoming_alert_no_channel_filter(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)

        # Simulate an alert group with channel filter deleted in the middle of the escalation
        # it should use the org default Slack channel to post the message to
        alert_group = make_alert_group(alert_receive_channel, channel_filter=None)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity, organization)
        step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @pytest.mark.django_db
    def test_process_signal_no_alert_group(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        alert = make_alert(alert_group=None, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        mock_chat_postMessage.assert_not_called()

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @pytest.mark.django_db
    def test_process_signal_channel_rate_limited(
        self,
        mock_chat_postMessage,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        organization, slack_team_identity = make_organization_with_slack_team_identity()

        # Set rate_limited_in_slack_at to a recent time to simulate rate limiting
        alert_receive_channel = make_alert_receive_channel(
            organization,
            rate_limited_in_slack_at=timezone.now() - timedelta(seconds=10),
        )
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        mock_chat_postMessage.assert_not_called()

        alert_group.refresh_from_db()
        assert alert_group.slack_message_sent is True
        assert alert_group.reason_to_skip_escalation == AlertGroup.RATE_LIMITED

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @pytest.mark.django_db
    def test_process_signal_no_slack_channel(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        organization = make_organization(default_slack_channel=None)
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel, channel_filter=None)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        alert_group.refresh_from_db()
        assert alert_group.slack_message_sent is False
        assert alert_group.reason_to_skip_escalation == AlertGroup.CHANNEL_NOT_SPECIFIED

        mock_chat_postMessage.assert_not_called()

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @pytest.mark.django_db
    def test_process_signal_debug_maintenance_mode(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_organization,
        make_slack_channel,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test the scenario where the alert receive channel is in DEBUG_MAINTENANCE mode.
        It should post the initial message and then send a debug mode notice in the same thread.
        """
        # Mock chat_postMessage to handle both calls
        # Set side_effect to return different values for each call
        mock_chat_postMessage.side_effect = [
            SLACK_POST_MESSAGE_SUCCESS_RESPONSE,  # create alert group slack message call return value
            {"ok": True},  # debug mode notice call return value
        ]

        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)

        alert_receive_channel = make_alert_receive_channel(
            organization,
            maintenance_mode=AlertReceiveChannel.DEBUG_MAINTENANCE,
        )

        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        # Ensure slack_message_sent is False initially
        assert not alert_group.slack_message_sent

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        assert mock_chat_postMessage.call_count == 2

        _, create_alert_group_slack_message_call_kwargs = mock_chat_postMessage.call_args_list[0]
        _, debug_mode_notice_call_kwargs = mock_chat_postMessage.call_args_list[1]

        assert create_alert_group_slack_message_call_kwargs["channel"] == slack_channel.slack_id

        text = "Escalations are silenced due to Debug mode"
        assert debug_mode_notice_call_kwargs == {
            "channel": slack_channel.slack_id,
            "text": text,
            "attachments": [],
            "thread_ts": SLACK_MESSAGE_TS,  # ts from first call
            "mrkdwn": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                    },
                },
            ],
        }

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        assert alert_group.slack_message_sent is True

        assert alert_group.slack_message is not None
        assert SlackMessage.objects.count() == 1
        assert alert_group.slack_message.slack_id == SLACK_MESSAGE_TS
        assert alert_group.slack_message.channel == slack_channel

        assert alert.delivered is True

    @patch("apps.slack.client.SlackClient.chat_postMessage", return_value=SLACK_POST_MESSAGE_SUCCESS_RESPONSE)
    @patch("apps.slack.scenarios.distribute_alerts.send_message_to_thread_if_bot_not_in_channel")
    @pytest.mark.django_db
    def test_process_signal_send_message_to_thread_if_bot_not_in_channel(
        self,
        mock_send_message_to_thread_if_bot_not_in_channel,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        assert alert_group.is_maintenance_incident is False
        assert alert_group.skip_escalation_in_slack is False

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        mock_send_message_to_thread_if_bot_not_in_channel.apply_async.assert_called_once_with(
            (alert_group.pk, slack_team_identity.pk, slack_channel.slack_id), countdown=1
        )

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @patch("apps.slack.models.SlackMessage.update_alert_groups_message")
    @pytest.mark.django_db
    def test_process_signal_update_existing_message(
        self,
        mock_update_alert_groups_message,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_slack_channel,
        make_slack_message,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)

        # Simulate that slack_message_sent is already True and skip_escalation_in_slack is False
        alert_group = make_alert_group(
            alert_receive_channel,
            slack_message_sent=True,
            reason_to_skip_escalation=AlertGroup.NO_REASON,
        )
        make_slack_message(slack_channel, alert_group=alert_group)

        assert alert_group.skip_escalation_in_slack is False

        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        # assert that the SlackMessage is updated, and that it is debounced
        mock_update_alert_groups_message.assert_called_once_with(debounce=True)
        mock_chat_postMessage.assert_not_called()

    @patch("apps.slack.client.SlackClient.chat_postMessage")
    @patch("apps.slack.models.SlackMessage.update_alert_groups_message")
    @pytest.mark.django_db
    def test_process_signal_do_not_update_due_to_skip_escalation(
        self,
        mock_update_alert_groups_message,
        mock_chat_postMessage,
        make_organization_with_slack_team_identity,
        make_slack_channel,
        make_slack_message,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test that when skip_escalation_in_slack is True, the update task is not scheduled.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        slack_channel = make_slack_channel(slack_team_identity)

        # Simulate that slack_message_sent is already True and skip escalation due to RATE_LIMITED
        alert_group = make_alert_group(
            alert_receive_channel,
            slack_message_sent=True,
            reason_to_skip_escalation=AlertGroup.RATE_LIMITED,  # Ensures skip_escalation_in_slack is True
        )
        alert = make_alert(alert_group, raw_request_data={})
        make_slack_message(slack_channel, alert_group=alert_group)

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        # assert that we don't update the SlackMessage
        mock_update_alert_groups_message.assert_not_called()
        mock_chat_postMessage.assert_not_called()

    @patch("apps.slack.client.SlackClient.chat_postMessage", side_effect=TimeoutError)
    @pytest.mark.django_db
    def test_process_signal_timeout_error(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        with pytest.raises(TimeoutError):
            step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        # Ensure that slack_message_sent is set back to False, this will allow us to retry.. a TimeoutError may have
        # been a transient error that is "recoverable"
        assert alert_group.slack_message_sent is False

        assert alert_group.slack_message is None
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered

    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @pytest.mark.parametrize(
        "reason,slack_error",
        [
            (reason, slack_error)
            for reason, slack_error in AlertGroup.REASONS_TO_SKIP_ESCALATIONS
            # we can skip NO_REASON because well this means theres no reason to skip the escalation
            # we can skip CHANNEL_NOT_SPECIFIED because this is handled "higher up" in process_signal
            if reason not in [AlertGroup.NO_REASON, AlertGroup.CHANNEL_NOT_SPECIFIED]
        ],
    )
    @pytest.mark.django_db
    def test_process_signal_slack_errors(
        self,
        mock_start_send_rate_limit_message_task,
        make_slack_team_identity,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_channel,
        reason,
        slack_error,
    ):
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)

        with patch.object(step._slack_client, "chat_postMessage") as mock_chat_postMessage:
            error_response = build_slack_response({"error": slack_error})
            error_class = get_error_class(error_response)
            slack_error_raised = error_class(error_response)
            mock_chat_postMessage.side_effect = slack_error_raised

            step.process_signal(alert)

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        if error_class == SlackAPIRatelimitError:
            mock_start_send_rate_limit_message_task.assert_called_once_with(
                "Delivering", slack_error_raised.retry_after
            )
        else:
            mock_start_send_rate_limit_message_task.assert_not_called()

        # For these Slack errors, retrying won't really help, so we should not set slack_message_sent back to False
        assert alert_group.slack_message_sent is True

        assert alert_group.reason_to_skip_escalation == reason
        assert alert_group.slack_message is None
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered

    @patch("apps.alerts.models.AlertReceiveChannel.start_send_rate_limit_message_task")
    @patch(
        "apps.slack.client.SlackClient.chat_postMessage",
        side_effect=SlackAPIRatelimitError(build_slack_response({"error": "ratelimited"})),
    )
    @pytest.mark.django_db
    def test_process_signal_slack_api_ratelimit_for_maintenance_integration(
        self,
        mock_chat_postMessage,
        mock_start_send_rate_limit_message_task,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test that when a SlackAPIRatelimitError occurs for a maintenance integration,
        the exception is re-raised and slack_message_sent is set back to False.
        """
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(
            organization, integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE
        )

        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)

        with pytest.raises(SlackAPIRatelimitError):
            step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        alert_group.refresh_from_db()

        mock_start_send_rate_limit_message_task.assert_not_called()

        # Ensure that slack_message_sent is set back to False, this will allow us to retry.. a SlackAPIRatelimitError,
        # may have been a transient error that is "recoverable"
        #
        # NOTE: we only want to retry for maintenance integrations, for other integrations we should not retry (this
        # case is tested above under test_process_signal_slack_errors)
        assert alert_group.slack_message_sent is False

        assert alert_group.reason_to_skip_escalation == AlertGroup.NO_REASON  # Should remain unchanged
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered

    @patch(
        "apps.slack.client.SlackClient.chat_postMessage",
        side_effect=SlackAPIFetchMembersFailedError(build_slack_response({"error": "fetch_members_failed"})),
    )
    @pytest.mark.django_db
    def test_process_signal_unhandled_slack_error(
        self,
        mock_chat_postMessage,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test that when an unhandled SlackAPIError occurs, the exception is re-raised
        and slack_message_sent is set back to False.
        """
        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)

        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)

        with pytest.raises(SlackAPIFetchMembersFailedError):
            step.process_signal(alert)

        mock_chat_postMessage.assert_called_once_with(
            channel=slack_channel.slack_id,
            attachments=alert_group.render_slack_attachments(),
            blocks=alert_group.render_slack_blocks(),
        )

        alert_group.refresh_from_db()

        # For these Slack errors that we don't explictly want to handle, retrying won't really help, so we should not
        # set slack_message_sent back to False
        assert alert_group.slack_message_sent is False

        assert alert_group.reason_to_skip_escalation == AlertGroup.NO_REASON  # Should remain unchanged
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered
