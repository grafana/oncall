from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroupLogRecord


@pytest.mark.django_db
def test_skip_update_signal(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    for skip_type in AlertGroupLogRecord.TYPES_SKIPPING_UPDATE_SIGNAL:
        with patch("apps.alerts.tasks.send_update_log_report_signal") as mock_update_log_signal:
            alert_group.log_records.create(type=skip_type)
        assert not mock_update_log_signal.apply_async.called


@pytest.mark.django_db
def test_trigger_update_signal(
    make_organization_with_slack_team_identity,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_with_slack_team_identity()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    for log_type, _ in AlertGroupLogRecord.TYPE_CHOICES:
        if log_type in AlertGroupLogRecord.TYPES_SKIPPING_UPDATE_SIGNAL:
            continue
        with patch("apps.alerts.tasks.send_update_log_report_signal") as mock_update_log_signal:
            alert_group.log_records.create(type=log_type)
        mock_update_log_signal.apply_async.assert_called_once()
