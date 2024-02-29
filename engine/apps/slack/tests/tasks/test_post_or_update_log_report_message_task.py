from unittest.mock import patch

import pytest

from apps.slack.scenarios.distribute_alerts import UpdateLogReportMessageStep
from apps.slack.tasks import post_or_update_log_report_message_task


@pytest.fixture()
def mock_update_log_report_message_step_post_log_message(monkeypatch):
    def mock_post_log_message(*args, **kwargs):
        return None

    monkeypatch.setattr(UpdateLogReportMessageStep, "post_log_message", mock_post_log_message)


@pytest.fixture()
def mock_update_log_report_message_step_update_log_message(monkeypatch):
    def mock_update_log_message(*args, **kwargs):
        return None

    monkeypatch.setattr(UpdateLogReportMessageStep, "update_log_message", mock_update_log_message)


@patch.object(UpdateLogReportMessageStep, "post_log_message")
@patch.object(UpdateLogReportMessageStep, "update_log_message")
@pytest.mark.django_db
@pytest.mark.parametrize("update_flag", [True, False])
def test_post_or_update_log_report_message_task_when_log_disabled(
    mock_update_log_report_message_step_post_log_message,
    mock_update_log_report_message_step_update_log_message,
    make_slack_team_identity,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    update_flag,
):
    slack_team_identity = make_slack_team_identity()
    organization = make_organization(is_slack_alert_group_log_enabled=False, slack_team_identity=slack_team_identity)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.skip_escalation_in_slack == False
    assert alert_group.channel.is_rate_limited_in_slack == False
    assert alert_group.channel.organization.is_slack_alert_group_log_enabled == False

    post_or_update_log_report_message_task(
        alert_group_pk=alert_group.pk, slack_team_identity_pk=slack_team_identity.pk, update=update_flag
    )

    mock_update_log_report_message_step_post_log_message.assert_not_called()
    mock_update_log_report_message_step_update_log_message.assert_not_called()
