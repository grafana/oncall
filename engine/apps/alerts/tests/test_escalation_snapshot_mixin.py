import datetime
from unittest.mock import PropertyMock, patch

import pytest
import pytz
from rest_framework.exceptions import ValidationError

from apps.alerts.escalation_snapshot.snapshot_classes import EscalationSnapshot
from apps.alerts.models import EscalationPolicy

MOCK_SLACK_CHANNEL_ID = "asdfljaskdf"
EMPTY_RAW_ESCALATION_SNAPSHOT = {
    "channel_filter_snapshot": None,
    "escalation_chain_snapshot": None,
    "last_active_escalation_policy_order": None,
    "escalation_policies_snapshots": [],
    "slack_channel_id": None,
    "pause_escalation": False,
    "next_step_eta": None,
}


@patch("apps.alerts.models.alert_group.AlertGroup.slack_channel_id", new_callable=PropertyMock)
@pytest.mark.django_db
def test_build_raw_escalation_snapshot_escalation_chain_exists(
    mock_alert_group_slack_channel_id,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    mock_alert_group_slack_channel_id.return_value = MOCK_SLACK_CHANNEL_ID

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    expected_snapshot = EscalationSnapshot.serializer(
        {
            "channel_filter_snapshot": alert_group.channel_filter,
            "escalation_chain_snapshot": alert_group.channel_filter.escalation_chain,
            "escalation_policies_snapshots": alert_group.channel_filter.escalation_chain.escalation_policies.all(),
            "slack_channel_id": MOCK_SLACK_CHANNEL_ID,
        }
    )

    assert alert_group.build_raw_escalation_snapshot() == expected_snapshot.data


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.pause_escalation",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_build_raw_escalation_snapshot_escalation_chain_does_not_exist_escalation_paused(
    mocked_pause_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
):
    mocked_pause_escalation.return_value = True

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    # Check that setting pause_escalation to True doesn't make the snapshot empty
    assert alert_group.build_raw_escalation_snapshot() != EMPTY_RAW_ESCALATION_SNAPSHOT


@pytest.mark.django_db
def test_build_raw_escalation_snapshot_escalation_chain_does_not_exist_no_channel_filter(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.build_raw_escalation_snapshot() == EMPTY_RAW_ESCALATION_SNAPSHOT


@pytest.mark.django_db
def test_build_raw_escalation_snapshot_escalation_chain_does_not_exist_no_channel_filter_escalation_chain(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.build_raw_escalation_snapshot() == EMPTY_RAW_ESCALATION_SNAPSHOT


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.channel_filter_snapshot",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_channel_filter_with_respect_to_escalation_snapshot(
    mock_channel_filter_snapshot,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    channel_filter_snapshot = "asdfasdfadsfadsf"
    mock_channel_filter_snapshot.return_value = channel_filter_snapshot

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.channel_filter_with_respect_to_escalation_snapshot == channel_filter_snapshot


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.channel_filter_snapshot",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_channel_filter_with_respect_to_escalation_snapshot_no_channel_filter_snapshot(
    mock_channel_filter_snapshot,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    mock_channel_filter_snapshot.return_value = None

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.channel_filter_with_respect_to_escalation_snapshot == channel_filter


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.escalation_chain_snapshot",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_escalation_chain_with_respect_to_escalation_snapshot(
    mock_escalation_chain_snapshot,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    escalation_chain_snapshot = "asdfasdfadsfadsf"
    mock_escalation_chain_snapshot.return_value = escalation_chain_snapshot

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.escalation_chain_with_respect_to_escalation_snapshot == escalation_chain_snapshot


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.escalation_chain_snapshot",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_escalation_chain_with_respect_to_escalation_snapshot_no_escalation_chain_snapshot(
    mock_escalation_chain_snapshot,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
):
    mock_escalation_chain_snapshot.return_value = None

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.escalation_chain_with_respect_to_escalation_snapshot == escalation_chain

    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.channel_filter is None
    assert alert_group.escalation_chain_with_respect_to_escalation_snapshot is None


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.escalation_chain_snapshot",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_escalation_chain_with_respect_to_escalation_snapshot_no_escalation_chain_snapshot_and_no_channel_filter(
    mock_escalation_chain_snapshot,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    mock_escalation_chain_snapshot.return_value = None

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.escalation_chain_with_respect_to_escalation_snapshot is None


@pytest.mark.django_db
def test_channel_filter_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.channel_filter_snapshot.id == channel_filter.id


@pytest.mark.django_db
def test_channel_filter_snapshot_no_escalation_chain_exists(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot["channel_filter_snapshot"] is None
    assert alert_group.channel_filter_snapshot is None


@pytest.mark.django_db
def test_channel_filter_snapshot_no_alert_group_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.channel_filter_snapshot is None


@pytest.mark.django_db
def test_escalation_chain_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.escalation_chain_snapshot.id == escalation_chain.id


@pytest.mark.django_db
def test_escalation_chain_snapshot_no_escalation_chain_exists(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot["escalation_chain_snapshot"] is None
    assert alert_group.escalation_chain_snapshot is None


@pytest.mark.django_db
def test_escalation_chain_snapshot_no_alert_group_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.escalation_chain_snapshot is None


@pytest.mark.django_db
def test_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    return_value = "asdfasdfasdf"
    with patch(
        "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin._deserialize_escalation_snapshot",
        return_value=return_value,
    ):
        assert alert_group.escalation_snapshot == return_value


@pytest.mark.django_db
def test_escalation_snapshot_validation_error(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    with patch(
        "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin._deserialize_escalation_snapshot",
        side_effect=ValidationError("asdfasdf"),
    ):
        assert alert_group.escalation_snapshot is None


@pytest.mark.django_db
def test_escalation_snapshot_no_alert_group_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.escalation_snapshot is None


@pytest.mark.django_db
def test_escalation_snapshot_empty_escalation_policies_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.has_escalation_policies_snapshots is False


@pytest.mark.django_db
def test_escalation_snapshot_nonempty_escalation_policies_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.has_escalation_policies_snapshots is True


@pytest.mark.django_db
def test_has_escalation_policies_snapshots_no_alert_group_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.raw_escalation_snapshot is None
    assert alert_group.has_escalation_policies_snapshots is False


@patch("apps.alerts.models.alert_group.AlertGroup.slack_channel_id", new_callable=PropertyMock)
@pytest.mark.django_db
def test_deserialize_escalation_snapshot(
    mock_alert_group_slack_channel_id,
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    mock_alert_group_slack_channel_id.return_value = MOCK_SLACK_CHANNEL_ID

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    escalation_policy = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    deserialized_escalation_snapshot = alert_group._deserialize_escalation_snapshot(alert_group.raw_escalation_snapshot)

    assert deserialized_escalation_snapshot.alert_group == alert_group
    assert deserialized_escalation_snapshot.channel_filter_snapshot.id == channel_filter.id
    assert deserialized_escalation_snapshot.escalation_chain_snapshot.id == escalation_chain.id
    assert deserialized_escalation_snapshot.last_active_escalation_policy_order is None
    assert len(deserialized_escalation_snapshot.escalation_policies_snapshots) == 1
    assert deserialized_escalation_snapshot.escalation_policies_snapshots[0].id == escalation_policy.id
    assert deserialized_escalation_snapshot.slack_channel_id == MOCK_SLACK_CHANNEL_ID
    assert deserialized_escalation_snapshot.pause_escalation is False
    assert deserialized_escalation_snapshot.next_step_eta is None
    assert deserialized_escalation_snapshot.stop_escalation is False


@pytest.mark.django_db
def test_escalation_chain_exists(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.pause_escalation is False
    assert alert_group.escalation_chain_exists is True


@patch(
    "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.pause_escalation",
    new_callable=PropertyMock,
)
@pytest.mark.django_db
def test_escalation_chain_exists_paused_escalation(
    mocked_pause_escalation,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    mocked_pause_escalation.return_value = True

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.pause_escalation is True
    assert alert_group.escalation_chain_exists is False


@pytest.mark.django_db
def test_escalation_chain_exists_no_channel_filter(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.pause_escalation is False
    assert alert_group.channel_filter is None
    assert alert_group.escalation_chain_exists is False


@pytest.mark.django_db
def test_escalation_chain_exists_no_channel_filter_escalation_chain(
    make_organization_and_user,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    assert alert_group.pause_escalation is False
    assert alert_group.channel_filter == channel_filter
    assert alert_group.channel_filter.escalation_chain is None
    assert alert_group.escalation_chain_exists is False


@pytest.mark.django_db
def test_pause_escalation_no_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.raw_escalation_snapshot is None
    assert alert_group.pause_escalation is False


@pytest.mark.django_db
def test_pause_escalation_raw_escalation_snapshot_exists(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.raw_escalation_snapshot["pause_escalation"] is False

    alert_group.raw_escalation_snapshot["pause_escalation"] = True

    assert alert_group.pause_escalation is True


@pytest.mark.django_db
def test_next_step_eta_no_raw_escalation_snapshot(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_group.raw_escalation_snapshot is None
    assert alert_group.next_step_eta is None


@pytest.mark.django_db
def test_next_step_eta_no_next_step_eta(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.raw_escalation_snapshot["next_step_eta"] is None
    assert alert_group.next_step_eta is None


@patch("apps.alerts.escalation_snapshot.escalation_snapshot_mixin.parse")
@pytest.mark.django_db
def test_next_step_eta(
    mock_dateutil_parser,
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    mocked_raw_date = "mcvnmcvmnvc"
    mocked_parsed_date = "asdfasdfaf"
    mock_dateutil_parser.return_value.replace.return_value = mocked_parsed_date

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = mocked_raw_date

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.raw_escalation_snapshot["next_step_eta"] is mocked_raw_date
    assert alert_group.next_step_eta == mocked_parsed_date

    mock_dateutil_parser.assert_called_once_with(mocked_raw_date)
    mock_dateutil_parser.return_value.replace.assert_called_once_with(tzinfo=pytz.UTC)


@pytest.mark.django_db
def test_update_next_step_eta(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    raw_next_step_eta = "2023-08-28T09:27:26.627047Z"
    updated_raw_next_step_eta = "2023-08-28T11:27:26.627047Z"
    increase_by_timedelta = datetime.timedelta(minutes=120)

    organization, _ = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.raw_escalation_snapshot["next_step_eta"] = raw_next_step_eta

    assert alert_group.raw_escalation_snapshot is not None
    assert alert_group.raw_escalation_snapshot["next_step_eta"] == raw_next_step_eta

    alert_group.update_next_step_eta(increase_by_timedelta)
    alert_group.save()
    alert_group.refresh_from_db()

    assert alert_group.raw_escalation_snapshot["next_step_eta"] == updated_raw_next_step_eta
