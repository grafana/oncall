from unittest.mock import Mock, PropertyMock, call, patch

import pytest
import requests
from django.test import override_settings
from django.utils import timezone

from apps.alerts.tasks.check_escalation_finished import (
    AlertGroupEscalationPolicyExecutionAuditException,
    audit_alert_group_escalation,
    check_escalation_finished_task,
    send_alert_group_escalation_auditor_task_heartbeat,
)

MOCKED_HEARTBEAT_URL = "https://hello.com/lsdjjkf"

now = timezone.now()
yesterday = now - timezone.timedelta(days=1)


@pytest.fixture
def make_alert_group_that_started_at_specific_date(make_alert_group):
    def _make_alert_group_that_started_at_specific_date(alert_receive_channel, started_at=yesterday, **kwargs):
        # we can't simply pass started_at to the fixture because started_at is being "auto-set" on the Model
        alert_group = make_alert_group(alert_receive_channel, **kwargs)
        alert_group.started_at = started_at
        alert_group.save()

        return alert_group

    return _make_alert_group_that_started_at_specific_date


def assert_not_called_with(self, *args, **kwargs):
    """
    https://stackoverflow.com/a/54838760
    """
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError("Expected %s to not have been called." % self._format_mock_call_signature(args, kwargs))


Mock.assert_not_called_with = assert_not_called_with


@patch("apps.alerts.tasks.check_escalation_finished.requests")
def test_send_alert_group_escalation_auditor_task_heartbeat_does_not_call_the_heartbeat_url_if_one_is_not_configured(
    mock_requests,
):
    send_alert_group_escalation_auditor_task_heartbeat()
    mock_requests.get.assert_not_called()


@patch("apps.alerts.tasks.check_escalation_finished.requests")
@override_settings(ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL=MOCKED_HEARTBEAT_URL)
def test_send_alert_group_escalation_auditor_task_heartbeat_calls_the_heartbeat_url_if_one_is_configured(mock_requests):
    send_alert_group_escalation_auditor_task_heartbeat()

    mock_requests.get.assert_called_once_with(MOCKED_HEARTBEAT_URL)
    mock_requests.get.return_value.raise_for_status.assert_called_once_with()


@patch("apps.alerts.tasks.check_escalation_finished.requests")
@override_settings(ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL=MOCKED_HEARTBEAT_URL)
def test_send_alert_group_escalation_auditor_task_heartbeat_raises_an_exception_if_the_heartbeat_url_request_fails(
    mock_requests,
):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError

    mock_requests.get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        send_alert_group_escalation_auditor_task_heartbeat()

    mock_requests.get.assert_called_once_with(MOCKED_HEARTBEAT_URL)
    mock_requests.get.return_value.raise_for_status.assert_called_once_with()


@pytest.mark.django_db
def test_audit_alert_group_escalation_skips_validation_if_the_alert_group_does_not_have_an_escalation_chain(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    alert_group.escalation_snapshot = None
    alert_group.save()

    assert alert_group.escalation_chain_exists is False

    try:
        audit_alert_group_escalation(alert_group)
    except AlertGroupEscalationPolicyExecutionAuditException:
        pytest.fail()


@pytest.mark.django_db
def test_audit_alert_group_escalation_raises_exception_if_the_alert_group_does_not_have_an_escalation_snapshot(
    escalation_snapshot_test_setup,
):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    alert_group.escalation_snapshot = None

    with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException):
        audit_alert_group_escalation(alert_group)


@pytest.mark.django_db
def test_audit_alert_group_escalation_skips_further_validation_if_the_escalation_policies_snapshots_is_empty(
    escalation_snapshot_test_setup,
):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    alert_group.escalation_snapshot.escalation_policies_snapshots = []
    audit_alert_group_escalation(alert_group)

    alert_group.escalation_snapshot.escalation_policies_snapshots = None
    audit_alert_group_escalation(alert_group)


@patch("apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.next_step_eta_is_valid")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "next_step_eta_is_valid_return_value,raises_exception",
    [
        (None, False),
        (True, False),
        (False, True),
    ],
)
def test_audit_alert_group_escalation_next_step_eta_validation(
    mock_next_step_eta_is_valid, escalation_snapshot_test_setup, next_step_eta_is_valid_return_value, raises_exception
):
    mock_next_step_eta_is_valid.return_value = next_step_eta_is_valid_return_value
    alert_group, _, _, _ = escalation_snapshot_test_setup

    if raises_exception:
        with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException):
            audit_alert_group_escalation(alert_group)
    else:
        try:
            audit_alert_group_escalation(alert_group)
        except AlertGroupEscalationPolicyExecutionAuditException:
            pytest.fail()

    mock_next_step_eta_is_valid.assert_called_once_with()


@patch(
    "apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.executed_escalation_policy_snapshots",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_audit_alert_group_escalation_no_executed_escalation_policy_snapshots(
    mock_executed_escalation_policy_snapshots, escalation_snapshot_test_setup
):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    mock_executed_escalation_policy_snapshots.return_value = []
    audit_alert_group_escalation(alert_group)
    mock_executed_escalation_policy_snapshots.assert_called_once_with()


# # see TODO: comment in engine/apps/alerts/tasks/check_escalation_finished.py
# @pytest.mark.django_db
# def test_audit_alert_group_escalation_all_executed_escalation_policy_snapshots_have_triggered_log_records(
#     escalation_snapshot_test_setup,
#     make_organization_and_user,
#     make_alert_group_log_record,
# ):
#     _, user = make_organization_and_user()
#     alert_group, _, _, _ = escalation_snapshot_test_setup
#     escalation_policies_snapshots = alert_group.escalation_snapshot.escalation_policies_snapshots

#     for escalation_policy_snapshot in escalation_policies_snapshots:
#         escalation_policy = EscalationPolicy.objects.get(id=escalation_policy_snapshot.id)
#         log_record_type = _get_relevant_log_record_type()

#         make_alert_group_log_record(alert_group, log_record_type, user, escalation_policy=escalation_policy)

#     with patch(
#         "apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.executed_escalation_policy_snapshots",
#         new_callable=PropertyMock,
#     ) as mock_executed_escalation_policy_snapshots:
#         mock_executed_escalation_policy_snapshots.return_value = escalation_policies_snapshots
#         audit_alert_group_escalation(alert_group)
#         mock_executed_escalation_policy_snapshots.assert_called_once_with()

# see TODO: comment in engine/apps/alerts/tasks/check_escalation_finished.py
# @pytest.mark.django_db
# def test_audit_alert_group_escalation_one_executed_escalation_policy_snapshot_does_not_have_a_triggered_log_record(
#     escalation_snapshot_test_setup,
#     make_organization_and_user,
#     make_alert_group_log_record,
# ):
#     _, user = make_organization_and_user()
#     alert_group, _, _, _ = escalation_snapshot_test_setup
#     escalation_policies_snapshots = alert_group.escalation_snapshot.escalation_policies_snapshots

#     # let's skip creating a relevant alert group log record for the first executed escalation policy
#     for idx, escalation_policy_snapshot in enumerate(escalation_policies_snapshots):
#         if idx != 0:
#             escalation_policy = EscalationPolicy.objects.get(id=escalation_policy_snapshot.id)
#             make_alert_group_log_record(
#                 alert_group, _get_relevant_log_record_type(), user, escalation_policy=escalation_policy
#             )

#     with patch(
#         "apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.executed_escalation_policy_snapshots",
#         new_callable=PropertyMock,
#     ) as mock_executed_escalation_policy_snapshots:
#         mock_executed_escalation_policy_snapshots.return_value = escalation_policies_snapshots

#         with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException):
#             audit_alert_group_escalation(alert_group)
#             mock_executed_escalation_policy_snapshots.assert_called_once_with()


@patch("apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation")
@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_queries_doesnt_grab_alert_groups_outside_of_date_range(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel)
    make_alert_group_that_started_at_specific_date(alert_receive_channel, now - timezone.timedelta(days=5))
    make_alert_group_that_started_at_specific_date(alert_receive_channel, now + timezone.timedelta(days=5))

    check_escalation_finished_task()

    mocked_audit_alert_group_escalation.assert_called_once_with(alert_group1)
    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@patch("apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation")
@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_calls_audit_alert_group_escalation_for_every_alert_group(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel)
    alert_group2 = make_alert_group_that_started_at_specific_date(alert_receive_channel)
    alert_group3 = make_alert_group_that_started_at_specific_date(alert_receive_channel)

    check_escalation_finished_task()

    mocked_audit_alert_group_escalation.assert_any_call(alert_group1)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group2)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group3)

    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@patch("apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation")
@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_filters_the_right_alert_groups(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel)

    silenced_for_one_hour_alert_group = make_alert_group_that_started_at_specific_date(
        alert_receive_channel, silenced=True, silenced_until=(now + timezone.timedelta(hours=1))
    )
    silenced_forever = make_alert_group_that_started_at_specific_date(
        alert_receive_channel, silenced=True, silenced_until=None
    )

    in_maintenance = make_alert_group_that_started_at_specific_date(alert_receive_channel, maintenance_uuid="asdfasdf")
    escalation_finished = make_alert_group_that_started_at_specific_date(
        alert_receive_channel, is_escalation_finished=True
    )

    resolved = make_alert_group_that_started_at_specific_date(alert_receive_channel, is_escalation_finished=True)
    acknowledged = make_alert_group_that_started_at_specific_date(alert_receive_channel, is_escalation_finished=True)

    root_alert_group = make_alert_group_that_started_at_specific_date(
        alert_receive_channel, root_alert_group=alert_group1
    )

    check_escalation_finished_task()

    mocked_audit_alert_group_escalation.assert_has_calls(
        [
            call(alert_group1),
            call(silenced_for_one_hour_alert_group),
        ],
        any_order=True,
    )

    mocked_audit_alert_group_escalation.assert_not_called_with(in_maintenance)
    mocked_audit_alert_group_escalation.assert_not_called_with(escalation_finished)

    mocked_audit_alert_group_escalation.assert_not_called_with(silenced_forever)
    mocked_audit_alert_group_escalation.assert_not_called_with(resolved)
    mocked_audit_alert_group_escalation.assert_not_called_with(acknowledged)

    mocked_audit_alert_group_escalation.assert_not_called_with(root_alert_group)


@patch("apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation")
@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_simply_calls_heartbeat_when_no_alert_groups_found(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
):
    check_escalation_finished_task()
    mocked_audit_alert_group_escalation.assert_not_called()
    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@patch("apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation")
@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_calls_audit_alert_group_escalation_for_every_alert_group_even_if_one_fails(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel)
    alert_group2 = make_alert_group_that_started_at_specific_date(alert_receive_channel)
    alert_group3 = make_alert_group_that_started_at_specific_date(alert_receive_channel)

    def _mocked_audit_alert_group_escalation(alert_group):
        if not alert_group.id == alert_group3.id:
            raise AlertGroupEscalationPolicyExecutionAuditException("asdfasdf")

    mocked_audit_alert_group_escalation.side_effect = _mocked_audit_alert_group_escalation

    with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException) as exc:
        check_escalation_finished_task()

    error_msg = str(exc.value)

    assert "The following alert group id(s) failed auditing:" in error_msg
    assert str(alert_group1.id) in error_msg
    assert str(alert_group2.id) in error_msg

    mocked_audit_alert_group_escalation.assert_any_call(alert_group1)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group2)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group3)

    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_not_called()
