from unittest.mock import patch

import pytest

from apps.slack.tasks import update_alert_group_slack_message


class TestUpdateAlertGroupSlackMessageTask:
    @patch("apps.slack.tasks.AlertGroupSlackService.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_slack_message_not_found(
        self,
        mock_update_alert_group_slack_message,
    ):
        """
        Test that the task exist early if SlackMessage does not exist.
        """
        update_alert_group_slack_message.apply((99999,), task_id="task-id")

        mock_update_alert_group_slack_message.assert_not_called()

    @patch("apps.slack.tasks.AlertGroupSlackService.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_task_id_mismatch(
        self,
        mock_update_alert_group_slack_message,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that the task exits early if current_task_id doesn't match active_update_task_id.
        """
        organization, _ = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        slack_message = make_slack_message(alert_group=alert_group)
        slack_message.active_update_task_id = "original-task-id"
        slack_message.save()

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="different-task-id")

        mock_update_alert_group_slack_message.assert_not_called()

    @patch("apps.slack.tasks.AlertGroupSlackService.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_no_alert_group(
        self,
        mock_update_alert_group_slack_message,
        make_organization,
        make_slack_message,
    ):
        """
        Test that the task exits early if SlackMessage has no alert_group.
        """
        slack_message = make_slack_message(alert_group=None, organization=make_organization())
        slack_message.active_update_task_id = "task-id"
        slack_message.save()

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        mock_update_alert_group_slack_message.assert_not_called()

    @patch("apps.slack.tasks.AlertGroupSlackService.update_alert_group_slack_message")
    @pytest.mark.django_db
    def test_update_alert_group_slack_message_successful(
        self,
        mock_update_alert_group_slack_message,
        make_organization_with_slack_team_identity,
        make_alert_receive_channel,
        make_slack_message,
        make_alert_group,
    ):
        """
        Test that the task successfully updates the alert group slack message.
        """
        organization, _ = make_organization_with_slack_team_identity()
        alert_receive_channel = make_alert_receive_channel(organization)
        alert_group = make_alert_group(alert_receive_channel)
        slack_message = make_slack_message(alert_group=alert_group)
        slack_message.active_update_task_id = "task-id"
        slack_message.save()

        update_alert_group_slack_message.apply((slack_message.pk,), task_id="task-id")

        # Assert that the service was called
        mock_update_alert_group_slack_message.assert_called_once_with(alert_group)

        # Verify that active_update_task_id is cleared and last_updated is set
        slack_message.refresh_from_db()
        assert slack_message.active_update_task_id is None
        assert slack_message.last_updated is not None
