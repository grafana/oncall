import datetime

import pytest

from apps.alerts.incident_appearance.templaters import AlertSlackTemplater
from apps.alerts.models import EscalationPolicy


@pytest.fixture()
def mock_alert_renderer_render_for(monkeypatch):
    def mock_render_for(*args, **kwargs):
        return "invalid_render_for"

    monkeypatch.setattr(AlertSlackTemplater, "_render_for", mock_render_for)


@pytest.fixture()
def escalation_snapshot_test_setup(
    make_organization_and_user,
    make_user_for_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
):
    organization, user_1 = make_organization_and_user()
    user_2 = make_user_for_organization(organization)

    alert_receive_channel = make_alert_receive_channel(organization)

    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        escalation_chain=escalation_chain,
        notification_backends={"BACKEND": {"channel_id": "abc123"}},
    )

    notify_to_multiple_users_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    notify_to_multiple_users_step.notify_to_users_queue.set([user_1, user_2])
    wait_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )
    # random time for test
    from_time = datetime.time(10, 30)
    to_time = datetime.time(18, 45)
    notify_if_time_step = make_escalation_policy(
        escalation_chain=channel_filter.escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_IF_TIME,
        from_time=from_time,
        to_time=to_time,
    )

    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()
    return alert_group, notify_to_multiple_users_step, wait_step, notify_if_time_step
