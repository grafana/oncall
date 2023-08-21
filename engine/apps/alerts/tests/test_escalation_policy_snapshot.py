from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.constants import NEXT_ESCALATION_DELAY
from apps.alerts.escalation_snapshot.serializers.escalation_policy_snapshot import EscalationPolicySnapshotSerializer
from apps.alerts.escalation_snapshot.snapshot_classes import EscalationPolicySnapshot
from apps.alerts.escalation_snapshot.utils import eta_for_escalation_step_notify_if_time
from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar


def get_escalation_policy_snapshot_from_model(escalation_policy):
    raw_escalation_policy_data = EscalationPolicySnapshotSerializer(escalation_policy).data
    escalation_policy_data = EscalationPolicySnapshotSerializer().to_internal_value(raw_escalation_policy_data)
    escalation_policy_snapshot = EscalationPolicySnapshot(**escalation_policy_data)
    return escalation_policy_snapshot


@pytest.fixture()
def escalation_step_test_setup(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)

    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    reason = "test escalation step"
    return organization, user, alert_receive_channel, channel_filter, alert_group, reason


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_wait(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup
    wait_delay = EscalationPolicy.FIFTEEN_MINUTES
    wait_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=wait_delay,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(wait_step)
    now = timezone.now()
    result = escalation_policy_snapshot.execute(alert_group, reason)

    assert result.eta is not None
    assert wait_delay + timezone.timedelta(minutes=1) > result.eta - now >= wait_delay
    assert result.stop_escalation is False and result.pause_escalation is False and result.start_from_beginning is False
    assert wait_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert not mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_all(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    notify_all_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_FINAL_NOTIFYALL,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_all_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)

    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_users_queue(
    mocked_execute_tasks,
    make_user_for_organization,
    escalation_step_test_setup,
    make_escalation_policy,
):
    organization, user, _, channel_filter, alert_group, reason = escalation_step_test_setup
    user_2 = make_user_for_organization(organization)

    notify_queue_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
    )
    notify_queue_step.notify_to_users_queue.set([user, user_2])
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_queue_step)

    assert escalation_policy_snapshot.next_user_in_sorted_queue == escalation_policy_snapshot.sorted_users_queue[0]

    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert escalation_policy_snapshot.next_user_in_sorted_queue == escalation_policy_snapshot.sorted_users_queue[1]
    assert notify_queue_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_multiple_users(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, user, _, channel_filter, alert_group, reason = escalation_step_test_setup

    notify_users_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    notify_users_step.notify_to_users_queue.set([user])
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_users_step)

    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert notify_users_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_on_call_schedule(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
    make_schedule,
    make_on_call_shift,
):
    organization, user, _, channel_filter, alert_group, reason = escalation_step_test_setup

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    # create on_call_shift with user to notify
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)
    schedule.custom_on_call_shifts.add(on_call_shift)

    notify_schedule_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=schedule,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_schedule_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert notify_schedule_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert list(escalation_policy_snapshot.notify_to_users_queue) == list(list_users_to_notify_from_ical(schedule))
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_on_call_schedule_viewer_user(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_user_for_organization,
    make_escalation_policy,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, channel_filter, alert_group, reason = escalation_step_test_setup
    viewer = make_user_for_organization(organization=organization, role=LegacyAccessControlRole.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    # create on_call_shift with user to notify
    start_date = timezone.now().replace(microsecond=0)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=7200),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(viewer)
    schedule.custom_on_call_shifts.add(on_call_shift)

    notify_schedule_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_SCHEDULE,
        notify_schedule=schedule,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_schedule_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert notify_schedule_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED).exists()
    assert list(escalation_policy_snapshot.notify_to_users_queue) == []
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_user_group(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_slack_team_identity,
    make_slack_user_group,
    make_escalation_policy,
):
    organization, _, _, channel_filter, alert_group, reason = escalation_step_test_setup
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()
    user_group = make_slack_user_group(slack_team_identity)

    notify_user_group_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_GROUP,
        notify_to_group=user_group,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_user_group_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_if_time(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    # current time is not between from_time and to_time, step returns eta
    now = timezone.now()
    from_time = (now - timezone.timedelta(hours=2)).time()
    to_time = (now - timezone.timedelta(hours=1)).time()
    notify_if_time_step_1 = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_TIME,
        from_time=from_time,
        to_time=to_time,
    )

    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_if_time_step_1)
    estimated_time_of_arrival = eta_for_escalation_step_notify_if_time(from_time, to_time)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=estimated_time_of_arrival,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert estimated_time_of_arrival is not None

    result = escalation_policy_snapshot.execute(alert_group, reason)

    assert result == expected_result
    assert notify_if_time_step_1.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert not mocked_execute_tasks.called

    # current time is between from_time and to_time, eta is None
    from_time = (now - timezone.timedelta(hours=2)).time()
    to_time = (now + timezone.timedelta(hours=1)).time()
    notify_if_time_step_2 = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_TIME,
        from_time=from_time,
        to_time=to_time,
    )

    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_if_time_step_2)
    estimated_time_of_arrival = eta_for_escalation_step_notify_if_time(from_time, to_time)
    assert estimated_time_of_arrival is None

    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)

    assert result == expected_result
    assert notify_if_time_step_2.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert not mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_notify_if_num_alerts_in_window(
    mocked_execute_tasks, escalation_step_test_setup, make_escalation_policy, make_alert
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    make_alert(alert_group=alert_group, raw_request_data={})
    make_alert(alert_group=alert_group, raw_request_data={})

    notify_if_3_alerts_per_1_minute = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
        num_alerts_in_window=3,
        num_minutes_in_window=1,
    )

    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_if_3_alerts_per_1_minute)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=True,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert notify_if_3_alerts_per_1_minute.log_records.filter(
        type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED
    ).exists()
    assert not mocked_execute_tasks.called

    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    make_alert(alert_group=alert_group, raw_request_data={})

    notify_if_1_alert = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW,
        num_alerts_in_window=1,
        num_minutes_in_window=2,
    )

    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(notify_if_1_alert)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert not mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_trigger_custom_button(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_custom_action,
    make_escalation_policy,
):
    organization, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    custom_button = make_custom_action(organization=organization)

    trigger_custom_button_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON,
        custom_button_trigger=custom_button,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(trigger_custom_button_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_trigger_custom_webhook(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_custom_webhook,
    make_escalation_policy,
):
    organization, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    custom_webhook = make_custom_webhook(organization=organization)

    trigger_custom_webhook_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON,
        custom_webhook=custom_webhook,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(trigger_custom_webhook_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_repeat_escalation_n_times(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    repeat_escalation_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_REPEAT_ESCALATION_N_TIMES,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(repeat_escalation_step)

    assert escalation_policy_snapshot.escalation_counter == 0

    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=True,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert escalation_policy_snapshot.escalation_counter == 1
    assert result == expected_result
    assert repeat_escalation_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert not mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_resolve(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    resolve_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_FINAL_RESOLVE,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(resolve_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=True,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert resolve_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED).exists()
    assert mocked_execute_tasks.called


@patch("apps.alerts.escalation_snapshot.snapshot_classes.EscalationPolicySnapshot._execute_tasks", return_value=None)
@pytest.mark.django_db
def test_escalation_step_is_not_configured(
    mocked_execute_tasks,
    escalation_step_test_setup,
    make_escalation_policy,
):
    _, _, _, channel_filter, alert_group, reason = escalation_step_test_setup

    not_configured_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=None,
    )
    escalation_policy_snapshot = get_escalation_policy_snapshot_from_model(not_configured_step)
    expected_eta = timezone.now() + timezone.timedelta(seconds=NEXT_ESCALATION_DELAY)
    result = escalation_policy_snapshot.execute(alert_group, reason)
    expected_result = EscalationPolicySnapshot.StepExecutionResultData(
        eta=result.eta,
        stop_escalation=False,
        pause_escalation=False,
        start_from_beginning=False,
    )
    assert expected_eta + timezone.timedelta(seconds=15) > result.eta > expected_eta - timezone.timedelta(seconds=15)
    assert result == expected_result
    assert not_configured_step.log_records.filter(type=AlertGroupLogRecord.TYPE_ESCALATION_FAILED).exists()
    assert not mocked_execute_tasks.called


@pytest.mark.django_db
def test_escalation_step_with_deleted_user(
    escalation_step_test_setup,
    make_user_for_organization,
    make_escalation_policy,
):
    """
    Test that deleted user in escalation policy snapshot will be simply ignored instead of ValidationError
    """
    organization, user, _, channel_filter, _, _ = escalation_step_test_setup
    inactive_user = make_user_for_organization(organization=organization, is_active=False)

    escalation_policy = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    escalation_policy.notify_to_users_queue.set([user, inactive_user])
    raw_snapshot = {
        "id": escalation_policy.pk,
        "order": 0,
        "step": escalation_policy.step,
        "wait_delay": None,
        "notify_to_users_queue": [user.pk, inactive_user.pk],
        "last_notified_user": None,
        "from_time": None,
        "to_time": None,
        "num_alerts_in_window": None,
        "num_minutes_in_window": None,
        "custom_button_trigger": None,
        "notify_schedule": None,
        "notify_to_group": None,
        "escalation_counter": 0,
        "passed_last_time": None,
        "pause_escalation": False,
    }

    deserialized_escalation_snapshot = EscalationPolicySnapshotSerializer().to_internal_value(raw_snapshot)
    assert deserialized_escalation_snapshot["notify_to_users_queue"] == [user]
