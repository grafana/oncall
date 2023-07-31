from unittest.mock import PropertyMock, patch

import pytest

from apps.alerts.models import Alert, EscalationPolicy
from apps.alerts.tasks import distribute_alert, escalate_alert_group


@pytest.mark.django_db
def test_alert_create_default_channel_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert alert.group.channel_filter == channel_filter


@pytest.mark.django_db
def test_alert_create_custom_channel_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_channel_filter(alert_receive_channel, is_default=True)
    other_channel_filter = make_channel_filter(alert_receive_channel)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        channel_filter=other_channel_filter,
    )

    assert alert.group.channel_filter == other_channel_filter


@pytest.mark.django_db
def test_distribute_alert_escalate_alert_group(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_escalation_chain,
    make_escalation_policy,
):
    """
    Check escalate_alert_group is called for the first alert in the group and not called for the second alert in the group.
    """
    organization = make_organization()
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    # Check escalate_alert_group is called for the first alert in the group
    alert_1 = make_alert(
        alert_group=alert_group,
        is_the_first_alert_in_group=True,
        raw_request_data=alert_receive_channel.config.example_payload,
    )
    with patch.object(escalate_alert_group, "apply_async") as mock_escalate_alert_group_1:
        distribute_alert(alert_1.pk)
    mock_escalate_alert_group_1.assert_called_once()

    # Check escalate_alert_group is not called for the second alert in the group
    alert_2 = make_alert(
        alert_group=alert_group,
        is_the_first_alert_in_group=False,
        raw_request_data=alert_receive_channel.config.example_payload,
    )
    with patch.object(escalate_alert_group, "apply_async") as mock_escalate_alert_group_2:
        distribute_alert(alert_2.pk)
    mock_escalate_alert_group_2.assert_not_called()


@pytest.mark.django_db
def test_distribute_alert_escalate_alert_group_when_escalation_paused(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
    make_escalation_chain,
    make_escalation_policy,
):
    """
    Check escalate_alert_group is called for the first alert in the group and for the second alert in the group when
    escalation is paused.
    """
    organization = make_organization()
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)

    # Check escalate_alert_group is called for the first alert in the group
    alert_1 = make_alert(
        alert_group=alert_group,
        is_the_first_alert_in_group=True,
        raw_request_data=alert_receive_channel.config.example_payload,
    )
    with patch.object(escalate_alert_group, "apply_async") as mock_escalate_alert_group_1:
        distribute_alert(alert_1.pk)
    mock_escalate_alert_group_1.assert_called_once()

    # Check escalate_alert_group is called for the second alert in the group when escalation is paused
    alert_2 = make_alert(
        alert_group=alert_group,
        is_the_first_alert_in_group=False,
        raw_request_data=alert_receive_channel.config.example_payload,
    )
    with patch(
        "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.pause_escalation",
        new_callable=PropertyMock(return_value=True),
    ):
        with patch.object(escalate_alert_group, "apply_async") as mock_escalate_alert_group_2:
            distribute_alert(alert_2.pk)
    mock_escalate_alert_group_2.assert_called_once()
