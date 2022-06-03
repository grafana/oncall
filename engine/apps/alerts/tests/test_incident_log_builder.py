import pytest

from apps.alerts.incident_log_builder import IncidentLogBuilder
from apps.alerts.models import EscalationPolicy
from apps.base.models import UserNotificationPolicy


@pytest.mark.django_db
def test_escalation_plan_messaging_backends(
    make_organization_and_user,
    make_user_notification_policy,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TESTONLY,
    )
    escalation_chain = make_escalation_chain(organization=organization)
    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
        last_notified_user=user,
    )
    escalation_policy.notify_to_users_queue.set([user])
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    log_builder = IncidentLogBuilder(alert_group=alert_group)
    plan = log_builder.get_incident_escalation_plan()
    assert list(plan.values()) == [["send test only backend message to {}".format(user.username)]]
