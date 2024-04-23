from unittest.mock import Mock, PropertyMock, call, patch

import pytest
import requests
from django.test import override_settings
from django.utils import timezone

from apps.alerts.models import EscalationPolicy
from apps.alerts.tasks.check_escalation_finished import (
    AlertGroupEscalationPolicyExecutionAuditException,
    audit_alert_group_escalation,
    check_alert_group_personal_notifications_task,
    check_escalation_finished_task,
    check_personal_notifications_task,
    send_alert_group_escalation_auditor_task_heartbeat,
)
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.twilioapp.models import TwilioSMS, TwilioSMSstatuses

MOCKED_HEARTBEAT_URL = "https://hello.com/lsdjjkf"

now = timezone.now()
yesterday = now - timezone.timedelta(days=1)


@pytest.fixture
def make_alert_group_that_started_at_specific_date(make_alert_group):
    def _make_alert_group_that_started_at_specific_date(
        alert_receive_channel, started_at=yesterday, received_delta=1, **kwargs
    ):
        # we can't simply pass started_at to the fixture because started_at is being "auto-set" on the Model
        alert_group = make_alert_group(alert_receive_channel, **kwargs)
        if received_delta is not None:
            alert_group.received_at = started_at - timezone.timedelta(seconds=received_delta)
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
def test_audit_alert_group_escalation_skips_validation_if_the_alert_group_does_not_have_an_escalation_chain_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    alert_group.raw_escalation_snapshot = {"escalation_chain_snapshot": None}
    alert_group.save()

    assert alert_group.raw_escalation_snapshot["escalation_chain_snapshot"] is None

    try:
        audit_alert_group_escalation(alert_group)
    except AlertGroupEscalationPolicyExecutionAuditException:
        pytest.fail()


@pytest.mark.django_db
def test_audit_alert_group_escalation_raises_exception_if_the_alert_group_does_not_have_an_escalation_snapshot(
    escalation_snapshot_test_setup,
):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    alert_group.raw_escalation_snapshot = None
    alert_group.save()

    with pytest.raises(AlertGroupEscalationPolicyExecutionAuditException):
        audit_alert_group_escalation(alert_group)


@pytest.mark.django_db
def test_audit_alert_group_escalation_skips_further_validation_if_the_escalation_policies_snapshots_is_empty(
    escalation_snapshot_test_setup,
):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    alert_group.escalation_snapshot.escalation_policies_snapshots = []
    alert_group.raw_escalation_snapshot = {"escalation_policies_snapshots": []}
    alert_group.save()
    audit_alert_group_escalation(alert_group)

    alert_group.raw_escalation_snapshot["escalation_policies_snapshots"] = None
    alert_group.save()
    audit_alert_group_escalation(alert_group)


@patch("apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.next_step_eta_is_valid")
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
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.last_active_escalation_policy_order",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_audit_alert_group_escalation_no_executed_escalation_policy_snapshots(
    mock_last_active_escalation_policy_order, escalation_snapshot_test_setup
):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    mock_last_active_escalation_policy_order.return_value = None
    audit_alert_group_escalation(alert_group)
    mock_last_active_escalation_policy_order.assert_called_once_with()


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
def test_check_escalation_finished_task_calls_audit_alert_group_escalation_for_every_alert_group_even_if_one_fails_and_returns_success_ratio(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    mocked_audit_alert_group_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
    caplog,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel, received_delta=1)
    alert_group2 = make_alert_group_that_started_at_specific_date(alert_receive_channel, received_delta=5)
    alert_group3 = make_alert_group_that_started_at_specific_date(alert_receive_channel, received_delta=12)
    alert_group3 = make_alert_group_that_started_at_specific_date(alert_receive_channel, received_delta=None)

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

    assert "Alert group ingestion/creation avg delta seconds: 6" in caplog.text
    assert "Alert group ingestion/creation max delta seconds: 12" in caplog.text
    assert "Alert group notifications success ratio: 25.00" in caplog.text

    mocked_audit_alert_group_escalation.assert_any_call(alert_group1)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group2)
    mocked_audit_alert_group_escalation.assert_any_call(alert_group3)

    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_not_called()


@patch("apps.alerts.tasks.check_escalation_finished.send_alert_group_escalation_auditor_task_heartbeat")
@pytest.mark.django_db
def test_check_escalation_finished_task_calls_audit_alert_group_personal_notifications(
    mocked_send_alert_group_escalation_auditor_task_heartbeat,
    make_organization_and_user,
    make_user_for_organization,
    make_user_notification_policy,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_alert_receive_channel,
    make_alert_group_that_started_at_specific_date,
    make_user_notification_policy_log_record,
    make_sms_record,
    caplog,
):
    organization, user = make_organization_and_user()
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )
    user2 = make_user_for_organization(organization)
    user_notification_policy2 = make_user_notification_policy(
        user=user2,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
    )
    # the previous one will be deleted later, we need to have an extra one (policy cannot be empty)
    make_user_notification_policy(
        user=user2,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SLACK,
    )

    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    notify_to_multiple_users_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    notify_to_multiple_users_step.notify_to_users_queue.set([user])

    alert_group1 = make_alert_group_that_started_at_specific_date(alert_receive_channel, channel_filter=channel_filter)
    alert_group2 = make_alert_group_that_started_at_specific_date(alert_receive_channel, channel_filter=channel_filter)
    alert_group3 = make_alert_group_that_started_at_specific_date(alert_receive_channel, channel_filter=channel_filter)
    alert_group4 = make_alert_group_that_started_at_specific_date(alert_receive_channel, channel_filter=channel_filter)
    alert_group5 = make_alert_group_that_started_at_specific_date(alert_receive_channel, channel_filter=channel_filter)
    alert_groups = [alert_group1, alert_group2, alert_group3, alert_group4, alert_group5]
    for alert_group in alert_groups:
        alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
        alert_group.raw_escalation_snapshot["last_active_escalation_policy_order"] = 1
        alert_group.save()

    now = timezone.now()
    # alert_group1: wait, notify user, notification successful
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group1,
        notification_policy=user_notification_policy,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        notification_step=UserNotificationPolicy.Step.WAIT,
    )
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group1,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group1,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
    )
    # records created > 5 mins ago
    alert_group1.personal_log_records.update(created_at=now - timezone.timedelta(minutes=7))

    # alert_group2: notify user, notification failed; triggered 2 sms, sent and accepted statuses
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group2,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group2,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
    )
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group2,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group2,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    # no failed or succeed record, but SMS was sent (without Twilio delivered confirmation yet)
    sms_record = make_sms_record(
        receiver=user,
        represents_alert_group=alert_group2,
        notification_policy=user_notification_policy,
    )
    sent_sms = TwilioSMS.objects.create(sid="someid", sms_record=sms_record, status=TwilioSMSstatuses.SENT)
    # no failed or succeed record, but SMS has status ACCEPTED from Twilio (without Twilio delivered confirmation yet)
    sms_record2 = make_sms_record(
        receiver=user,
        represents_alert_group=alert_group2,
        notification_policy=user_notification_policy,
    )
    accepted_sms = TwilioSMS.objects.create(sid="someid2", sms_record=sms_record2, status=TwilioSMSstatuses.ACCEPTED)
    # records created > 5 mins ago
    alert_group2.personal_log_records.update(created_at=now - timezone.timedelta(minutes=7))
    sent_sms.created_at = now - timezone.timedelta(minutes=6)
    sent_sms.save()
    accepted_sms.created_at = now - timezone.timedelta(minutes=6)
    accepted_sms.save()

    # alert_group3: notify user, missing completion
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group3,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    # record created > 5 mins ago
    alert_group3.personal_log_records.update(created_at=now - timezone.timedelta(minutes=7))

    # alert_group4: notify user created > 5 mins ago, missing completion
    make_user_notification_policy_log_record(
        author=user,
        created_at=now - timezone.timedelta(minutes=3),
        alert_group=alert_group3,
        notification_policy=user_notification_policy,
        notification_step=UserNotificationPolicy.Step.NOTIFY,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    # record created < 5 mins ago
    alert_group4.personal_log_records.update(created_at=now - timezone.timedelta(minutes=2))

    # alert_group5: notification triggered but policy is deleted before completion (should be ignored)
    make_user_notification_policy_log_record(
        author=user2,
        alert_group=alert_group5,
        notification_policy=user_notification_policy2,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        notification_step=UserNotificationPolicy.Step.WAIT,
    )
    user_notification_policy2.delete()

    # trigger task
    with patch(
        "apps.alerts.tasks.check_escalation_finished.check_alert_group_personal_notifications_task"
    ) as mock_check_notif:
        check_escalation_finished_task()

    for alert_group in alert_groups:
        mock_check_notif.apply_async.assert_any_call((alert_group.id,))
        check_alert_group_personal_notifications_task(alert_group.id)
        if alert_group == alert_group3:
            assert f"Alert group {alert_group3.id} has (1) uncompleted personal notifications" in caplog.text
        else:
            assert f"Alert group {alert_group.id} personal notifications check passed" in caplog.text

    mocked_send_alert_group_escalation_auditor_task_heartbeat.assert_called()

    # also trigger the general personal notification checker
    check_personal_notifications_task()

    assert "personal_notifications_triggered=6 personal_notifications_completed=2" in caplog.text
