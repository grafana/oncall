from unittest.mock import patch

import pytest

from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.alerts.tasks.bulk_action import bulk_alert_group_action


@pytest.fixture()
def alert_group_setup(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_resolved_ack_new_silenced_alert_groups,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    alert_groups = make_resolved_ack_new_silenced_alert_groups(alert_receive_channel, default_channel_filter, {})
    return user, organization, alert_groups


@patch("apps.alerts.tasks.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.apply_async", return_value=None)
@patch("apps.alerts.models.AlertGroup.start_escalation_if_needed", return_value=None)
@pytest.mark.django_db
def test_bulk_action_restart(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    mocked_start_escalate_alert,
    alert_group_setup,
):
    user, organization, alert_groups = alert_group_setup
    resolved_alert_group, acked_alert_group, new_alert_group, silenced_alert_group = alert_groups

    assert not resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert not acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert not silenced_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    # restart alert groups
    alert_group_pks = [alert_group.public_primary_key for alert_group in alert_groups]
    bulk_alert_group_action(AlertGroup.RESTART, None, alert_group_pks, user.pk, organization.id)

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert silenced_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called
    assert mocked_start_escalate_alert.called


@patch("apps.alerts.tasks.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.apply_async", return_value=None)
@pytest.mark.django_db
def test_bulk_action_acknowledge(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    make_user_auth_headers,
    alert_group_setup,
):
    user, organization, alert_groups = alert_group_setup
    resolved_alert_group, acked_alert_group, new_alert_group, _ = alert_groups

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    # acknowledge alert groups
    alert_group_pks = [alert_group.public_primary_key for alert_group in alert_groups]
    bulk_alert_group_action(AlertGroup.ACKNOWLEDGE, None, alert_group_pks, user.pk, organization.id)

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert not acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ACK,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called


@patch("apps.alerts.tasks.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.apply_async", return_value=None)
@pytest.mark.django_db
def test_bulk_action_resolve(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    make_user_auth_headers,
    alert_group_setup,
):
    user, organization, alert_groups = alert_group_setup
    resolved_alert_group, acked_alert_group, new_alert_group, _ = alert_groups

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    # resolve alert groups
    alert_group_pks = [alert_group.public_primary_key for alert_group in alert_groups]
    bulk_alert_group_action(AlertGroup.RESOLVE, None, alert_group_pks, user.pk, organization.id)

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert not resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_RESOLVED,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called


@patch("apps.alerts.tasks.send_alert_group_signal.apply_async", return_value=None)
@patch("apps.alerts.tasks.send_update_log_report_signal.apply_async", return_value=None)
@patch("apps.alerts.models.AlertGroup.start_unsilence_task", return_value=None)
@pytest.mark.django_db
def test_bulk_action_silence(
    mocked_alert_group_signal_task,
    mocked_log_report_signal_task,
    mocked_start_unsilence_task,
    make_user_auth_headers,
    alert_group_setup,
):
    user, organization, alert_groups = alert_group_setup
    resolved_alert_group, acked_alert_group, new_alert_group, silenced_alert_groups = alert_groups

    assert not new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    # silence alert groups
    alert_group_pks = [alert_group.public_primary_key for alert_group in alert_groups]
    bulk_alert_group_action(AlertGroup.SILENCE, 180, alert_group_pks, user.pk, organization.id)

    assert new_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    new_alert_group.refresh_from_db()
    assert new_alert_group.silenced

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_ACK,
        author=user,
    ).exists()

    assert acked_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
        author=user,
    ).exists()

    assert resolved_alert_group.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert silenced_alert_groups.log_records.filter(
        type=AlertGroupLogRecord.TYPE_UN_SILENCE,
        author=user,
    ).exists()

    assert silenced_alert_groups.log_records.filter(
        type=AlertGroupLogRecord.TYPE_SILENCE,
        author=user,
    ).exists()

    assert mocked_alert_group_signal_task.called
    assert mocked_log_report_signal_task.called
    assert mocked_start_unsilence_task.called
