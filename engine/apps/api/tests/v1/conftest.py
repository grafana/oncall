from datetime import timedelta

import pytest
from django.utils import timezone

from apps.slack.scenarios.distribute_alerts import AlertShootingStep
from apps.slack.slack_client import SlackClientWithErrorHandling


@pytest.fixture()
def mock_slack_api_call(monkeypatch):
    def _mock_api_call(*args, **kwargs):
        return {
            "status": 200,
            "user": {
                "profile": {"image_512": "TEST_SLACK_IMAGE_URL"},
                "name": "TEST_SLACK_LOGIN",
                "real_name": "TEST_SLACK_NAME",
            },
            "team": {"name": "TEST_SLACK_TEAM_NAME"},
        }

    monkeypatch.setattr(SlackClientWithErrorHandling, "api_call", _mock_api_call)


@pytest.fixture()
def make_resolved_ack_new_silenced_alert_groups(make_alert_group, make_alert_receive_channel, make_alert):
    def _make_alert_groups_all_statuses(alert_receive_channel, channel_filter, alert_raw_request_data, **kwargs):
        resolved_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=channel_filter,
            acknowledged_at=timezone.now() + timedelta(hours=1),
            resolved_at=timezone.now() + timedelta(hours=2),
            resolved=True,
            acknowledged=True,
        )
        make_alert(alert_group=resolved_alert_group, raw_request_data=alert_raw_request_data)

        ack_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=channel_filter,
            acknowledged_at=timezone.now() + timedelta(hours=1),
            acknowledged=True,
        )
        make_alert(alert_group=ack_alert_group, raw_request_data=alert_raw_request_data)

        new_alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
        make_alert(alert_group=new_alert_group, raw_request_data=alert_raw_request_data)

        silenced_alert_group = make_alert_group(
            alert_receive_channel,
            channel_filter=channel_filter,
            silenced=True,
            silenced_at=timezone.now() + timedelta(hours=1),
        )
        make_alert(alert_group=silenced_alert_group, raw_request_data=alert_raw_request_data)

        return resolved_alert_group, ack_alert_group, new_alert_group, silenced_alert_group

    return _make_alert_groups_all_statuses


@pytest.fixture()
def mock_alert_shooting_step_post_alert_group_to_slack(monkeypatch):
    def mock_post_alert_group_to_slack(*args, **kwargs):
        return None

    monkeypatch.setattr(AlertShootingStep, "_post_alert_group_to_slack", mock_post_alert_group_to_slack)
