from datetime import timedelta

import pytest
from django.utils import timezone

from apps.alerts.incident_appearance.templaters import AlertSlackTemplater


@pytest.fixture()
def mock_alert_renderer_render_for(monkeypatch):
    def mock_render_for(*args, **kwargs):
        return "invalid_render_for"

    monkeypatch.setattr(AlertSlackTemplater, "_render_for", mock_render_for)


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
