from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroup
from apps.slack.models import SlackMessage
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.slack_client.exceptions import SlackAPIException


@pytest.mark.django_db
def test_restricted_action_error(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    SlackAlertShootingStep = ScenarioStep.get_step("distribute_alerts", "AlertShootingStep")
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert = make_alert(alert_group, raw_request_data="{}")

    step = SlackAlertShootingStep(slack_team_identity)

    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        mock_slack_api_call.side_effect = SlackAPIException(response={"error": "restricted_action"})
        step._post_alert_group_to_slack(slack_team_identity, alert_group, alert, None, "channel-id", [])

    alert_group.refresh_from_db()
    alert.refresh_from_db()
    assert alert_group.reason_to_skip_escalation == AlertGroup.RESTRICTED_ACTION
    assert alert_group.slack_message is None
    assert SlackMessage.objects.count() == 0
    assert not alert.delivered
