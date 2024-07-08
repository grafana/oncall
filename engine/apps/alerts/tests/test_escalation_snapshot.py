import pytest
from django.utils import timezone

from apps.alerts.escalation_snapshot.snapshot_classes import (
    ChannelFilterSnapshot,
    EscalationPolicySnapshot,
    EscalationSnapshot,
)
from apps.alerts.models import EscalationPolicy


@pytest.mark.django_db
def test_raw_escalation_snapshot(escalation_snapshot_test_setup):
    alert_group, notify_to_multiple_users_step, wait_step, notify_if_time_step = escalation_snapshot_test_setup
    raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    expected_result = {
        "channel_filter_snapshot": {
            "id": alert_group.channel_filter.pk,
            "str_for_clients": alert_group.channel_filter.str_for_clients,
            "notify_in_slack": True,
            "notify_in_telegram": False,
            "notification_backends": alert_group.channel_filter.notification_backends,
        },
        "pause_escalation": False,
        "last_active_escalation_policy_order": None,
        "slack_channel_id": None,
        "next_step_eta": None,
        "escalation_chain_snapshot": {
            "id": notify_to_multiple_users_step.escalation_chain.pk,
            "name": notify_to_multiple_users_step.escalation_chain.name,
        },
        "escalation_policies_snapshots": [
            {
                "id": notify_to_multiple_users_step.pk,
                "order": 0,
                "step": EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
                "wait_delay": None,
                "notify_to_users_queue": [u.pk for u in notify_to_multiple_users_step.notify_to_users_queue.all()],
                "last_notified_user": None,
                "notify_schedule": None,
                "notify_to_group": None,
                "notify_to_team_members": None,
                "from_time": None,
                "to_time": None,
                "num_alerts_in_window": None,
                "num_minutes_in_window": None,
                "custom_webhook": None,
                "escalation_counter": 0,
                "passed_last_time": None,
                "pause_escalation": False,
            },
            {
                "id": wait_step.pk,
                "order": 1,
                "step": EscalationPolicy.STEP_WAIT,
                "wait_delay": "00:15:00",
                "notify_to_users_queue": [],
                "last_notified_user": None,
                "notify_schedule": None,
                "notify_to_group": None,
                "notify_to_team_members": None,
                "from_time": None,
                "to_time": None,
                "num_alerts_in_window": None,
                "num_minutes_in_window": None,
                "custom_webhook": None,
                "escalation_counter": 0,
                "passed_last_time": None,
                "pause_escalation": False,
            },
            {
                "id": notify_if_time_step.pk,
                "order": 2,
                "step": EscalationPolicy.STEP_NOTIFY_IF_TIME,
                "wait_delay": None,
                "notify_to_users_queue": [],
                "last_notified_user": None,
                "notify_schedule": None,
                "notify_to_group": None,
                "notify_to_team_members": None,
                "from_time": notify_if_time_step.from_time.isoformat(),
                "to_time": notify_if_time_step.to_time.isoformat(),
                "num_alerts_in_window": None,
                "num_minutes_in_window": None,
                "custom_webhook": None,
                "escalation_counter": 0,
                "passed_last_time": None,
                "pause_escalation": False,
            },
        ],
    }
    assert raw_escalation_snapshot == expected_result


@pytest.mark.django_db
def test_serialized_escalation_snapshot(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    escalation_snapshot = alert_group.escalation_snapshot
    assert isinstance(escalation_snapshot, EscalationSnapshot)
    assert escalation_snapshot.channel_filter_snapshot is not None and isinstance(
        escalation_snapshot.channel_filter_snapshot, ChannelFilterSnapshot
    )
    assert escalation_snapshot.escalation_policies_snapshots is not None and isinstance(
        escalation_snapshot.escalation_policies_snapshots[0], EscalationPolicySnapshot
    )
    assert (
        len(escalation_snapshot.escalation_policies_snapshots)
        == alert_group.channel_filter.escalation_chain.escalation_policies.count()
    )

    escalation_snapshot_dict = escalation_snapshot.convert_to_dict()

    assert alert_group.raw_escalation_snapshot == escalation_snapshot_dict


@pytest.mark.django_db
def test_escalation_snapshot_with_deleted_channel_filter(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    alert_group.channel_filter.delete()

    escalation_snapshot = alert_group.escalation_snapshot
    escalation_snapshot_dict = escalation_snapshot.convert_to_dict()

    assert alert_group.raw_escalation_snapshot == escalation_snapshot_dict


@pytest.mark.django_db
def test_change_escalation_snapshot(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup

    new_active_order = 2
    now = timezone.now()
    escalation_snapshot = alert_group.escalation_snapshot
    escalation_snapshot.last_active_escalation_policy_order = new_active_order
    escalation_snapshot.escalation_policies_snapshots[0].passed_last_time = now

    escalation_snapshot.save_to_alert_group()
    # rebuild escalation snapshot to be sure that changes was saved
    escalation_snapshot = alert_group.escalation_snapshot

    assert escalation_snapshot.last_active_escalation_policy_order == new_active_order
    assert escalation_snapshot.escalation_policies_snapshots[0].passed_last_time == now

    assert alert_group.raw_escalation_snapshot == escalation_snapshot.convert_to_dict()


@pytest.mark.django_db
def test_next_escalation_policy_snapshot(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    escalation_snapshot = alert_group.escalation_snapshot

    assert escalation_snapshot.last_active_escalation_policy_order is None
    assert escalation_snapshot.last_active_escalation_policy_snapshot is None
    assert (
        escalation_snapshot.next_active_escalation_policy_snapshot
        is escalation_snapshot.escalation_policies_snapshots[0]
    )

    escalation_snapshot.last_active_escalation_policy_order = 0

    assert escalation_snapshot.last_active_escalation_policy_order == 0
    assert (
        escalation_snapshot.last_active_escalation_policy_snapshot
        is escalation_snapshot.escalation_policies_snapshots[0]
    )
    assert (
        escalation_snapshot.next_active_escalation_policy_snapshot
        is escalation_snapshot.escalation_policies_snapshots[1]
    )

    escalation_policies_snapshots_count = len(escalation_snapshot.escalation_policies_snapshots)
    last_active_escalation_policy_order = escalation_policies_snapshots_count - 1
    escalation_snapshot.last_active_escalation_policy_order = last_active_escalation_policy_order

    assert escalation_snapshot.last_active_escalation_policy_order == last_active_escalation_policy_order
    assert (
        escalation_snapshot.last_active_escalation_policy_snapshot
        is escalation_snapshot.escalation_policies_snapshots[-1]
    )
    assert escalation_snapshot.next_active_escalation_policy_snapshot is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "timedelta,time_in_past,expected",
    [
        (None, None, None),
        (timezone.timedelta(weeks=50), True, False),
        (timezone.timedelta(minutes=4), True, True),
        (timezone.timedelta(minutes=4), False, True),
    ],
)
def test_next_step_eta_is_valid(escalation_snapshot_test_setup, timedelta, time_in_past, expected) -> None:
    now = timezone.now()

    if timedelta is None:
        next_step_eta = None
    elif time_in_past:
        next_step_eta = now - timedelta
    else:
        next_step_eta = now + timedelta

    alert_group, _, _, _ = escalation_snapshot_test_setup
    escalation_snapshot = alert_group.escalation_snapshot

    escalation_snapshot.next_step_eta = next_step_eta
    escalation_snapshot.save_to_alert_group()
    alert_group.refresh_from_db()

    assert alert_group.next_step_eta_is_valid() is expected


@pytest.mark.django_db
def test_executed_escalation_policy_snapshots(escalation_snapshot_test_setup):
    alert_group, _, _, _ = escalation_snapshot_test_setup
    escalation_snapshot = alert_group.escalation_snapshot

    escalation_snapshot.last_active_escalation_policy_order = None
    assert escalation_snapshot.executed_escalation_policy_snapshots == []

    escalation_snapshot.last_active_escalation_policy_order = 0
    assert escalation_snapshot.executed_escalation_policy_snapshots == [
        escalation_snapshot.escalation_policies_snapshots[0]
    ]

    escalation_snapshot.last_active_escalation_policy_order = len(escalation_snapshot.escalation_policies_snapshots) - 1
    assert escalation_snapshot.executed_escalation_policy_snapshots == escalation_snapshot.escalation_policies_snapshots


@pytest.mark.django_db
def test_escalation_snapshot_non_sequential_orders(
    make_organization,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_escalation_policy,
    make_alert_group,
):
    organization = make_organization()

    alert_receive_channel = make_alert_receive_channel(organization)

    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        escalation_chain=escalation_chain,
        notification_backends={"BACKEND": {"channel_id": "abc123"}},
    )

    step_1 = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        order=12,
    )
    step_2 = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        order=42,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    escalation_snapshot = alert_group.escalation_snapshot
    assert escalation_snapshot.last_active_escalation_policy_order is None
    assert escalation_snapshot.next_active_escalation_policy_snapshot.id == step_1.id

    escalation_snapshot.execute_actual_escalation_step()
    assert escalation_snapshot.last_active_escalation_policy_order == 0
    assert escalation_snapshot.next_active_escalation_policy_snapshot.id == step_2.id

    escalation_snapshot.execute_actual_escalation_step()
    assert escalation_snapshot.last_active_escalation_policy_order == 1
    assert escalation_snapshot.next_active_escalation_policy_snapshot is None

    policy_ids = [p.id for p in escalation_snapshot.executed_escalation_policy_snapshots]
    assert policy_ids == [step_1.id, step_2.id]


@pytest.mark.django_db
def test_serialize_escalation_snapshot_with_deleted_user(
    make_organization_and_user,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        escalation_chain=escalation_chain,
        notification_backends={"BACKEND": {"channel_id": "abc123"}},
    )

    notify_users_queue = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
        last_notified_user=user,
    )
    notify_users_queue.notify_to_users_queue.set([user])

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()
    escalation_snapshot = alert_group.escalation_snapshot

    assert notify_users_queue.last_notified_user == user
    assert escalation_snapshot.escalation_policies_snapshots[0].last_notified_user == user
    assert len(escalation_snapshot.escalation_policies_snapshots[0].notify_to_users_queue) == 1

    # delete user
    user.is_active = None
    user.save()

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    # clear cached_property
    del alert_group.escalation_snapshot
    alert_group.save()

    escalation_snapshot = alert_group.escalation_snapshot

    assert notify_users_queue.last_notified_user == user
    assert escalation_snapshot is not None
    assert escalation_snapshot.escalation_policies_snapshots[0].last_notified_user is None
    assert len(escalation_snapshot.escalation_policies_snapshots[0].notify_to_users_queue) == 0
