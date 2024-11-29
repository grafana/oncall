from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.slack.errors import SlackAPIError, get_error_class
from apps.slack.models import SlackMessage
from apps.slack.scenarios.distribute_alerts import IncomingAlertStep
from apps.slack.tests.conftest import build_slack_response
from apps.slack.utils import get_cache_key_update_incident_slack_message


class TestIncomingAlertStep:
    @pytest.mark.django_db
    def test_process_signal_success_first_message(
        self,
        make_organization_with_slack_team_identity,
        make_slack_channel,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test the success case where process_signal posts the first Slack message for the alert group.
        """
        # Set up organization and Slack identities
        organization, slack_team_identity = make_organization_with_slack_team_identity()

        # Create the Slack channel and set it as the default for the organization
        slack_channel = make_slack_channel(slack_team_identity)
        organization.default_slack_channel = slack_channel
        organization.save()

        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel, slack_message_sent=False)
        alert = make_alert(alert_group, raw_request_data="{}")

        # Ensure slack_message_sent is False initially
        assert not alert_group.slack_message_sent

        step = IncomingAlertStep(slack_team_identity)

        with patch.object(step._slack_client, "chat_postMessage") as mock_chat_postMessage:
            # Simulate successful response from Slack API
            mock_chat_postMessage.return_value = {"ts": "1234567890.123456"}

            step.process_signal(alert)

            mock_chat_postMessage.assert_called_once_with(
                channel=slack_channel.slack_id,
                attachments=alert_group.render_slack_attachments(),
                blocks=alert_group.render_slack_blocks(),
            )

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        # Check that slack_message_sent is now True
        assert alert_group.slack_message_sent is True

        # Check that a SlackMessage was created and associated correctly
        assert alert_group.slack_message is not None
        assert SlackMessage.objects.count() == 1
        assert alert_group.slack_message.slack_id == "1234567890.123456"
        assert alert_group.slack_message.channel == slack_channel

        # Check that the alert was marked as delivered
        assert alert.delivered is True

    @pytest.mark.parametrize("exception", [TimeoutError, SlackAPIError])
    @patch("apps.slack.scenarios.distribute_alerts.IncomingAlertStep._post_alert_group_to_slack")
    @pytest.mark.django_db
    def test_post_alert_group_to_slack_raises_error(
        self,
        mock_post_alert_group_to_slack,
        exception,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        if exception == SlackAPIError:
            mock_post_alert_group_to_slack.side_effect = exception(build_slack_response({"error": "test"}))
        else:
            mock_post_alert_group_to_slack.side_effect = exception

        slack_team_identity = make_slack_team_identity()
        slack_channel = make_slack_channel(slack_team_identity)
        organization = make_organization(slack_team_identity=slack_team_identity, default_slack_channel=slack_channel)
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data="{}")

        step = IncomingAlertStep(slack_team_identity)
        with pytest.raises(exception):
            step.process_signal(alert)

        mock_post_alert_group_to_slack.assert_called_once()

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        assert alert_group.slack_message is None
        assert alert_group.slack_message_sent is False
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered

    @patch("apps.slack.scenarios.distribute_alerts.IncomingAlertStep._post_alert_group_to_slack")
    @pytest.mark.django_db
    def test_incoming_alert_no_channel_filter(
        self,
        mock_post_alert_group_to_slack,
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

        assert mock_post_alert_group_to_slack.call_args[1]["slack_channel"] == slack_channel

    @patch("apps.slack.scenarios.distribute_alerts.IncomingAlertStep._post_alert_group_to_slack")
    @pytest.mark.django_db
    def test_process_signal_no_alert_group(
        self,
        mock_post_alert_group_to_slack,
        make_slack_team_identity,
        make_alert,
    ):
        slack_team_identity = make_slack_team_identity()
        alert = make_alert(alert_group=None, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        mock_post_alert_group_to_slack.assert_not_called()

    @pytest.mark.django_db
    def test_process_signal_channel_rate_limited(
        self,
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

        alert_group.refresh_from_db()
        assert alert_group.slack_message_sent is True
        assert alert_group.reason_to_skip_escalation == AlertGroup.RATE_LIMITED

    @patch("apps.slack.scenarios.distribute_alerts.IncomingAlertStep._post_alert_group_to_slack")
    @pytest.mark.django_db
    def test_process_signal_no_slack_channel(
        self,
        mock_post_alert_group_to_slack,
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

        mock_post_alert_group_to_slack.assert_not_called()

    @pytest.mark.django_db
    def test_process_signal_debug_maintenance_mode(
        self,
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

        # Mock chat_postMessage to handle both calls
        with patch.object(step._slack_client, "chat_postMessage") as mock_chat_postMessage:
            # Set side_effect to return different values for each call
            mock_chat_postMessage.side_effect = [
                {"ts": "1234567890.123456"},  # create alert group slack message call return value
                {"ok": True},  # debug mode notice call return value
            ]

            step.process_signal(alert)

            # Verify that chat_postMessage was called twice
            assert mock_chat_postMessage.call_count == 2

            # Get the call arguments for both calls
            _, create_alert_group_slack_message_call_kwargs = mock_chat_postMessage.call_args_list[0]
            _, debug_mode_notice_call_kwargs = mock_chat_postMessage.call_args_list[1]

            assert create_alert_group_slack_message_call_kwargs["channel"] == slack_channel.slack_id

            text = "Escalations are silenced due to Debug mode"
            assert debug_mode_notice_call_kwargs == {
                "channel": slack_channel.slack_id,
                "text": text,
                "attachments": [],
                "thread_ts": "1234567890.123456",  # ts from first call
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

        # Check that slack_message_sent is now True
        assert alert_group.slack_message_sent is True

        # Check that a SlackMessage was created and associated correctly
        assert alert_group.slack_message is not None
        assert SlackMessage.objects.count() == 1
        assert alert_group.slack_message.slack_id == "1234567890.123456"
        assert alert_group.slack_message.channel == slack_channel

        # Check that the alert was marked as delivered
        assert alert.delivered is True

    @patch("apps.slack.scenarios.distribute_alerts.IncomingAlertStep._post_alert_group_to_slack")
    @patch("apps.slack.scenarios.distribute_alerts.send_message_to_thread_if_bot_not_in_channel")
    @pytest.mark.django_db
    def test_process_signal_send_message_to_thread_if_bot_not_in_channel(
        self,
        mock_send_message_to_thread_if_bot_not_in_channel,
        _mock_post_alert_group_to_slack,
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

        mock_send_message_to_thread_if_bot_not_in_channel.apply_async.assert_called_once_with(
            (alert_group.pk, slack_team_identity.pk, slack_channel.slack_id), countdown=1
        )

    @patch("apps.slack.scenarios.distribute_alerts.update_incident_slack_message")
    @pytest.mark.django_db
    def test_process_signal_update_existing_message(
        self,
        mock_update_incident_slack_message,
        make_slack_team_identity,
        make_slack_channel,
        make_organization,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        mocked_update_incident_task_id = "1234"
        mock_update_incident_slack_message.apply_async.return_value = mocked_update_incident_task_id

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
        assert alert_group.skip_escalation_in_slack is False

        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        # assert that the background task is scheduled
        mock_update_incident_slack_message.apply_async.assert_called_once_with(
            (slack_team_identity.pk, alert_group.pk), countdown=10
        )

        # Verify that the cache is set correctly
        assert cache.get(get_cache_key_update_incident_slack_message(alert_group.pk)) == mocked_update_incident_task_id

    @patch("apps.slack.scenarios.distribute_alerts.update_incident_slack_message")
    @pytest.mark.django_db
    def test_process_signal_do_not_update_due_to_skip_escalation(
        self,
        mock_update_incident_slack_message,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
    ):
        """
        Test that when skip_escalation_in_slack is True, the update task is not scheduled.
        """
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)

        # Simulate that slack_message_sent is already True and skip escalation due to RATE_LIMITED
        alert_group = make_alert_group(
            alert_receive_channel,
            slack_message_sent=True,
            reason_to_skip_escalation=AlertGroup.RATE_LIMITED,  # Ensures skip_escalation_in_slack is True
        )
        alert = make_alert(alert_group, raw_request_data={})

        step = IncomingAlertStep(slack_team_identity)
        step.process_signal(alert)

        # assert that the background task is not scheduled
        mock_update_incident_slack_message.apply_async.assert_not_called()

    @pytest.mark.django_db
    def test_post_alert_group_to_slack_success(
        self,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_channel,
    ):
        """
        Test the success case where _post_alert_group_to_slack successfully posts a message to Slack.
        """
        organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data="{}")

        slack_channel = make_slack_channel(slack_team_identity)

        step = IncomingAlertStep(slack_team_identity)

        with patch.object(step._slack_client, "chat_postMessage") as mock_chat_postMessage:
            # Simulate successful response from Slack API
            mock_chat_postMessage.return_value = {"ts": "1234567890.123456"}

            step._post_alert_group_to_slack(alert_group, alert, None, slack_channel, [])

        alert_group.refresh_from_db()
        alert.refresh_from_db()

        assert alert_group.reason_to_skip_escalation == AlertGroup.NO_REASON
        assert alert_group.slack_message is not None
        assert SlackMessage.objects.count() == 1
        assert alert.delivered is True
        assert alert_group.slack_message.slack_id == "1234567890.123456"
        assert alert_group.slack_message.channel == slack_channel

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
    def test_post_alert_group_to_slack_errors(
        self,
        make_organization_and_user_with_slack_identities,
        make_alert_receive_channel,
        make_alert_group,
        make_alert,
        make_slack_channel,
        reason,
        slack_error,
    ):
        organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        alert = make_alert(alert_group, raw_request_data="{}")

        slack_channel = make_slack_channel(slack_team_identity)

        step = IncomingAlertStep(slack_team_identity)

        with patch.object(step._slack_client, "chat_postMessage") as mock_chat_postMessage:
            error_response = build_slack_response({"error": slack_error})
            error_class = get_error_class(error_response)
            mock_chat_postMessage.side_effect = error_class(error_response)

            step._post_alert_group_to_slack(alert_group, alert, None, slack_channel, [])

        alert_group.refresh_from_db()
        alert.refresh_from_db()
        assert alert_group.reason_to_skip_escalation == reason
        assert alert_group.slack_message is None
        assert SlackMessage.objects.count() == 0
        assert not alert.delivered
