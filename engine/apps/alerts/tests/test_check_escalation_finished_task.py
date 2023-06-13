from unittest.mock import Mock, PropertyMock, patch

import pytest
import requests
from django.test import override_settings
from django.utils import timezone

from apps.alerts.models import AlertGroup
from apps.alerts.tasks.check_escalation_finished import (
    AlertGroupEscalationPolicyExecutionAuditException,
    audit_alert_group_escalation,
    check_escalation_finished_task,
    send_alert_group_escalation_auditor_task_heartbeat,
)

MOCKED_HEARTBEAT_URL = "https://hello.com/lsdjjkf"


# def _get_relevant_log_record_type() -> int:
#     return random.choice([AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED, AlertGroupLogRecord.TYPE_ESCALATION_FAILED])


def test_send_alert_group_escalation_auditor_task_heartbeat_does_not_call_the_heartbeat_url_if_one_is_not_configured():
    with patch("apps.alerts.tasks.check_escalation_finished.requests") as mock_requests:
        send_alert_group_escalation_auditor_task_heartbeat()
        mock_requests.get.assert_not_called()


@override_settings(ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL=MOCKED_HEARTBEAT_URL)
def test_send_alert_group_escalation_auditor_task_heartbeat_calls_the_heartbeat_url_if_one_is_configured():
    with patch("apps.alerts.tasks.check_escalation_finished.requests") as mock_requests:
        send_alert_group_escalation_auditor_task_heartbeat()

        mock_requests.get.assert_called_once_with(MOCKED_HEARTBEAT_URL)
        mock_requests.get.return_value.raise_for_status.assert_called_once_with()


@override_settings(ALERT_GROUP_ESCALATION_AUDITOR_CELERY_TASK_HEARTBEAT_URL=MOCKED_HEARTBEAT_URL)
def test_send_alert_group_escalation_auditor_task_heartbeat_raises_an_exception_if_the_heartbeat_url_request_fails():
    with patch("apps.alerts.tasks.check_escalation_finished.requests") as mock_requests:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError

        mock_requests.get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            send_alert_group_escalation_auditor_task_heartbeat()

        mock_requests.get.assert_called_once_with(MOCKED_HEARTBEAT_URL)
        mock_requests.get.return_value.raise_for_status.assert_called_once_with()


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
    escalation_snapshot_test_setup, next_step_eta_is_valid_return_value, raises_exception
):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    with patch(
        "apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.next_step_eta_is_valid"
    ) as mock_next_step_eta_is_valid:
        mock_next_step_eta_is_valid.return_value = next_step_eta_is_valid_return_value

        if raises_exception:
            with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException):
                audit_alert_group_escalation(alert_group)
        else:
            try:
                audit_alert_group_escalation(alert_group)
            except AlertGroupEscalationPolicyExecutionAuditException:
                pytest.fail()

        mock_next_step_eta_is_valid.assert_called_once_with()


@pytest.mark.django_db
def test_audit_alert_group_escalation_no_executed_escalation_policy_snapshots(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    with patch(
        "apps.alerts.escalation_snapshot.snapshot_classes.escalation_snapshot.EscalationSnapshot.executed_escalation_policy_snapshots",
        new_callable=PropertyMock,
    ) as mock_executed_escalation_policy_snapshots:
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


@pytest.mark.django_db
def test_check_escalation_finished_task_queries_doesnt_grab_alert_groups_outside_of_date_range(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    now = timezone.now()
    two_days_ago = now - timezone.timedelta(days=2)
    two_days_in_future = now + timezone.timedelta(days=2)

    # we can't simply pass started_at to the fixture because started_at is being "auto-set" on the Model
    alert_group1 = make_alert_group(alert_receive_channel)
    alert_group1.started_at = now

    alert_group2 = make_alert_group(alert_receive_channel)
    alert_group2.started_at = now - timezone.timedelta(days=5)

    alert_group3 = make_alert_group(alert_receive_channel)
    alert_group3.started_at = now + timezone.timedelta(days=5)

    AlertGroup.all_objects.bulk_update([alert_group1, alert_group2, alert_group3], ["started_at"])

    with patch(
        "apps.alerts.tasks.check_escalation_finished.get_auditable_alert_groups_started_at_range"
    ) as mocked_get_auditable_alert_groups_started_at_range:
        with patch(
            "apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation"
        ) as mocked_audit_alert_group_escalation:
            with patch(
                "apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat"
            ) as mocked_send_alert_group_escalation_auditor_task_heartbeat:
                mocked_get_auditable_alert_groups_started_at_range.return_value = (two_days_ago, two_days_in_future)

                check_escalation_finished_task()

                mocked_audit_alert_group_escalation.assert_called_once_with(alert_group1)
                mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@pytest.mark.django_db
def test_check_escalation_finished_task_calls_audit_alert_group_escalation_for_every_alert_group(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    now = timezone.now()
    two_days_ago = now - timezone.timedelta(days=2)
    two_days_in_future = now + timezone.timedelta(days=2)

    # we can't simply pass started_at to the fixture because started_at is being "auto-set" on the Model
    alert_group1 = make_alert_group(alert_receive_channel)
    alert_group1.started_at = now

    alert_group2 = make_alert_group(alert_receive_channel)
    alert_group2.started_at = now

    alert_group3 = make_alert_group(alert_receive_channel)
    alert_group3.started_at = now

    AlertGroup.all_objects.bulk_update([alert_group1, alert_group2, alert_group3], ["started_at"])

    with patch(
        "apps.alerts.tasks.check_escalation_finished.get_auditable_alert_groups_started_at_range"
    ) as mocked_get_auditable_alert_groups_started_at_range:
        with patch(
            "apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation"
        ) as mocked_audit_alert_group_escalation:
            with patch(
                "apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat"
            ) as mocked_send_alert_group_escalation_auditor_task_heartbeat:
                mocked_get_auditable_alert_groups_started_at_range.return_value = (two_days_ago, two_days_in_future)

                check_escalation_finished_task()

                mocked_audit_alert_group_escalation.assert_any_call(alert_group1)
                mocked_audit_alert_group_escalation.assert_any_call(alert_group2)
                mocked_audit_alert_group_escalation.assert_any_call(alert_group3)
                mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@pytest.mark.django_db
def test_check_escalation_finished_task_simply_calls_heartbeat_when_no_alert_groups_found():
    with patch(
        "apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation"
    ) as mocked_audit_alert_group_escalation:
        with patch(
            "apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat"
        ) as mocked_send_alert_group_escalation_auditor_task_heartbeat:
            check_escalation_finished_task()
            mocked_audit_alert_group_escalation.assert_not_called()
            mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called_once_with()


@pytest.mark.django_db
def test_check_escalation_finished_task_calls_audit_alert_group_escalation_for_every_alert_group_even_if_one_fails(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    now = timezone.now()
    two_days_ago = now - timezone.timedelta(days=2)
    two_days_in_future = now + timezone.timedelta(days=2)

    # we can't simply pass started_at to the fixture because started_at is being "auto-set" on the Model
    alert_group1 = make_alert_group(alert_receive_channel)
    alert_group1.started_at = now

    alert_group2 = make_alert_group(alert_receive_channel)
    alert_group2.started_at = now

    alert_group3 = make_alert_group(alert_receive_channel)
    alert_group3.started_at = now

    AlertGroup.all_objects.bulk_update([alert_group1, alert_group2, alert_group3], ["started_at"])

    def _mocked_audit_alert_group_escalation(alert_group):
        if not alert_group.id == alert_group3.id:
            raise AlertGroupEscalationPolicyExecutionAuditException("asdfasdf")

    with patch(
        "apps.alerts.tasks.check_escalation_finished.get_auditable_alert_groups_started_at_range"
    ) as mocked_get_auditable_alert_groups_started_at_range:
        with patch(
            "apps.alerts.tasks.check_escalation_finished.audit_alert_group_escalation"
        ) as mocked_audit_alert_group_escalation:
            with patch(
                "apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat"
            ) as mocked_send_alert_group_escalation_auditor_task_heartbeat:
                mocked_get_auditable_alert_groups_started_at_range.return_value = (two_days_ago, two_days_in_future)
                mocked_audit_alert_group_escalation.side_effect = _mocked_audit_alert_group_escalation

                with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException) as exc:
                    check_escalation_finished_task()

                assert (
                    str(exc.value)
                    == f"The following alert group id(s) failed auditing: {alert_group1.id}, {alert_group2.id}"
                )

                mocked_audit_alert_group_escalation.assert_any_call(alert_group1)
                mocked_audit_alert_group_escalation.assert_any_call(alert_group2)
                mocked_audit_alert_group_escalation.assert_any_call(alert_group3)

                mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_not_called()
