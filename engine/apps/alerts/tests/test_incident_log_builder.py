import pytest
from django.utils import timezone

from apps.alerts.incident_log_builder import IncidentLogBuilder
from apps.alerts.models import EscalationPolicy
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord


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
    plan = log_builder.get_escalation_plan()
    assert list(plan.values()) == [["send test only backend message to {}".format(user.username)]]


@pytest.mark.django_db
def test_get_notification_plan_for_user_with_bundled_notification(
    make_organization_and_user,
    make_user_notification_bundle,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_policy_log_record,
):
    """
    Test building notification plan when one of the notifications was bundled:
    - test that scheduled but not triggered bundled notification appears in notification plan
    """

    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    log_builder = IncidentLogBuilder(alert_group)

    notification_bundle = make_user_notification_bundle(user, UserNotificationPolicy.NotificationChannel.SMS)
    notification_policy_sms = make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=UserNotificationPolicy.NotificationChannel.SMS
    )
    notification_policy_slack = make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=UserNotificationPolicy.NotificationChannel.SLACK
    )
    make_user_notification_policy(user, UserNotificationPolicy.Step.WAIT, wait_delay=timezone.timedelta(minutes=5))
    make_user_notification_policy(
        user, UserNotificationPolicy.Step.NOTIFY, notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL
    )

    # bundled SMS notification has been scheduled, the second notification step "Notify by Slack" has not been passed
    # SMS notification should appear in notification plan with timedelta=2min
    bundled_sms_notification = notification_bundle.notifications.create(
        alert_group=alert_group,
        notification_policy=notification_policy_sms,
        alert_receive_channel=alert_receive_channel,
    )
    notification_plan_dict = log_builder._get_notification_plan_for_user(user)
    expected_plan_dict = {
        timezone.timedelta(0): [
            {
                "user_id": user.id,
                "plan_lines": [f"invite {user.username} in Slack"],
                "is_the_first_notification_step": False,
            }
        ],
        timezone.timedelta(seconds=120): [{"user_id": user.id, "plan_lines": [f"send sms to {user.username}"]}],
        timezone.timedelta(seconds=300): [{"user_id": user.id, "plan_lines": [f"call {user.username} by phone"]}],
    }
    assert notification_plan_dict == expected_plan_dict

    # the second notification step "Notify by Slack" has been passed
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=notification_policy_slack,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    notification_plan_dict = log_builder._get_notification_plan_for_user(user)
    expected_plan_dict = {
        timezone.timedelta(0): [{"user_id": user.id, "plan_lines": [], "is_the_first_notification_step": False}],
        timezone.timedelta(seconds=120): [{"user_id": user.id, "plan_lines": [f"send sms to {user.username}"]}],
        timezone.timedelta(seconds=300): [{"user_id": user.id, "plan_lines": [f"call {user.username} by phone"]}],
    }
    assert notification_plan_dict == expected_plan_dict

    # bundled SMS notification has been triggered, it should not appear in notification plan anymore
    make_user_notification_policy_log_record(
        author=user,
        alert_group=alert_group,
        notification_policy=notification_policy_sms,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
    )
    bundled_sms_notification.bundle_uuid = "test_bundle_uuid"
    bundled_sms_notification.save()

    notification_plan_dict = log_builder._get_notification_plan_for_user(user)
    expected_plan_dict = {
        timezone.timedelta(0): [{"user_id": user.id, "plan_lines": [], "is_the_first_notification_step": False}],
        timezone.timedelta(seconds=300): [{"user_id": user.id, "plan_lines": [f"call {user.username} by phone"]}],
    }
    assert notification_plan_dict == expected_plan_dict


@pytest.mark.django_db
def test_escalation_plan_custom_webhooks(
    make_organization_and_user,
    make_escalation_chain,
    make_escalation_policy,
    make_custom_webhook,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    escalation_chain = make_escalation_chain(organization=organization)
    custom_webhook = make_custom_webhook(organization=organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.FIFTEEN_MINUTES,
    )
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK,
        custom_webhook=custom_webhook,
    )
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)
    alert_group = make_alert_group(alert_receive_channel, channel_filter=channel_filter)
    alert_group.raw_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
    alert_group.save()

    log_builder = IncidentLogBuilder(alert_group=alert_group)
    plan = log_builder.get_escalation_plan()
    assert list(plan.values()) == [[f'trigger outgoing webhook "{custom_webhook.name}"']]
