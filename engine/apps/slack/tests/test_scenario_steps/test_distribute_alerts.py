from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroup
from apps.slack.errors import get_error_class
from apps.slack.models import SlackMessage
from apps.slack.scenarios.distribute_alerts import AlertShootingStep
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.tests.conftest import build_slack_response


@pytest.mark.django_db
@pytest.mark.parametrize(
    "reason,slack_error",
    [
        (reason, slack_error)
        for reason, slack_error in AlertGroup.REASONS_TO_SKIP_ESCALATIONS
        if reason != AlertGroup.NO_REASON
    ],
)
def test_skip_escalations_error(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    reason,
    slack_error,
):
    SlackAlertShootingStep = ScenarioStep.get_step("distribute_alerts", "AlertShootingStep")
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group, raw_request_data="{}")

    step = SlackAlertShootingStep(slack_team_identity)

    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        error_response = build_slack_response({"error": slack_error})
        error_class = get_error_class(error_response)
        mock_slack_api_call.side_effect = error_class(error_response)
        channel_id = "channel-id"
        if reason == AlertGroup.CHANNEL_NOT_SPECIFIED:
            channel_id = None
        step._post_alert_group_to_slack(slack_team_identity, alert_group, alert, None, channel_id, [])

    alert_group.refresh_from_db()
    alert.refresh_from_db()
    assert alert_group.reason_to_skip_escalation == reason
    assert alert_group.slack_message is None
    assert SlackMessage.objects.count() == 0
    assert not alert.delivered


@pytest.mark.django_db
def test_timeout_error(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    SlackAlertShootingStep = ScenarioStep.get_step("distribute_alerts", "AlertShootingStep")
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity, general_log_slack_channel=slack_channel)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group, raw_request_data="{}")

    step = SlackAlertShootingStep(slack_team_identity)

    with pytest.raises(TimeoutError):
        with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
            mock_slack_api_call.side_effect = TimeoutError
            step.process_signal(alert)

    alert_group.refresh_from_db()
    alert.refresh_from_db()
    assert alert_group.slack_message is None
    assert alert_group.slack_message_sent is False
    assert SlackMessage.objects.count() == 0
    assert not alert.delivered


@patch.object(AlertShootingStep, "_post_alert_group_to_slack")
@pytest.mark.django_db
def test_alert_shooting_no_channel_filter(
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
    organization = make_organization(slack_team_identity=slack_team_identity, general_log_slack_channel=slack_channel)
    alert_receive_channel = make_alert_receive_channel(organization)

    # simulate an alert group with channel filter deleted in the middle of the escalation
    alert_group = make_alert_group(alert_receive_channel, channel_filter=None)
    alert = make_alert(alert_group, raw_request_data={})

    step = AlertShootingStep(slack_team_identity, organization)
    step.process_signal(alert)

    mock_post_alert_group_to_slack.assert_called_once()
    assert mock_post_alert_group_to_slack.call_args[1]["channel_id"] == "DEFAULT_CHANNEL_ID"
