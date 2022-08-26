import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.alerts.models import AlertGroupLogRecord, EscalationPolicy
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.schedules.models import OnCallScheduleCalendar
from apps.telegram.models import TelegramMessage
from apps.twilioapp.constants import TwilioCallStatuses, TwilioMessageStatuses


@pytest.mark.django_db
def test_organization_delete(
    make_organization,
    make_user,
    make_team,
    make_slack_team_identity,
    make_slack_user_identity,
    make_slack_message,
    make_slack_action_record,
    make_schedule,
    make_custom_action,
    make_alert_receive_channel,
    make_escalation_chain,
    make_escalation_policy,
    make_channel_filter,
    make_user_notification_policy,
    make_telegram_user_connector,
    make_telegram_channel,
    make_telegram_verification_code,
    make_telegram_channel_verification_code,
    make_telegram_message,
    make_alert,
    make_alert_group,
    make_alert_group_log_record,
    make_user_notification_policy_log_record,
    make_sms,
    make_phone_call,
    make_token_for_organization,
    make_public_api_token,
    make_invitation,
    make_resolution_note,
    make_resolution_note_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    organization = make_organization(slack_team_identity=slack_team_identity)

    slack_user_identity_1 = make_slack_user_identity(slack_team_identity=slack_team_identity, slack_id="USER_1")
    slack_user_identity_2 = make_slack_user_identity(slack_team_identity=slack_team_identity, slack_id="USER_2")

    user_1 = make_user(organization=organization, slack_user_identity=slack_user_identity_1)
    user_2 = make_user(organization=organization, slack_user_identity=slack_user_identity_2)

    user_notification_policy = make_user_notification_policy(
        user=user_1, step=UserNotificationPolicy.Step.WAIT, wait_delay=timezone.timedelta(minutes=15), important=False
    )

    team = make_team(organization=organization)
    team.users.add(user_1)

    schedule = make_schedule(organization=organization, schedule_class=OnCallScheduleCalendar)
    custom_action = make_custom_action(organization=organization)

    escalation_chain = make_escalation_chain(organization=organization)
    escalation_policy = make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_WAIT,
        wait_delay=EscalationPolicy.ONE_MINUTE,
        last_notified_user=user_1,
    )
    escalation_policy.notify_to_users_queue.set([user_1, user_2])

    alert_receive_channel = make_alert_receive_channel(organization=organization, author=user_1)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True, escalation_chain=escalation_chain)

    alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_by_user=user_1,
        silenced_by_user=user_2,
        wiped_by=user_2,
    )

    alert = make_alert(alert_group=alert_group, raw_request_data={})
    alert_group.resolved_by_alert = alert
    alert_group.save(update_fields=["resolved_by_alert"])

    user_notification_policy_log_record = make_user_notification_policy_log_record(
        author=user_1,
        type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
        notification_policy=user_notification_policy,
        notification_step=user_notification_policy.step,
        notification_channel=user_notification_policy.notify_by,
        alert_group=alert_group,
    )

    sms = make_sms(
        receiver=user_1, status=TwilioMessageStatuses.SENT, represents_alert=alert, represents_alert_group=alert_group
    )

    phone_call = make_phone_call(
        receiver=user_1, status=TwilioCallStatuses.COMPLETED, represents_alert=alert, represents_alert_group=alert_group
    )

    telegram_user_connector = make_telegram_user_connector(user=user_1)
    telegram_channel = make_telegram_channel(organization=organization)
    telegram_verification_code = make_telegram_verification_code(user=user_1)
    telegram_channel_verification_code = make_telegram_channel_verification_code(
        organization=organization, author=user_1
    )
    telegram_message = make_telegram_message(alert_group=alert_group, message_type=TelegramMessage.ALERT_GROUP_MESSAGE)

    slack_message = make_slack_message(alert_group=alert_group)
    slack_action_record = make_slack_action_record(organization=organization, user=user_1)

    plugin_token, _ = make_token_for_organization(organization)
    public_api_token, _ = make_public_api_token(user_1, organization)

    invitation = make_invitation(alert_group=alert_group, author=user_1, invitee=user_2)

    alert_group_log_record = make_alert_group_log_record(
        alert_group=alert_group, author=user_1, type=AlertGroupLogRecord.TYPE_ACK, invitation=invitation
    )

    resolution_note_slack_message = make_resolution_note_slack_message(
        alert_group=alert_group, user=user_1, added_by_user=user_2
    )
    resolution_note = make_resolution_note(
        alert_group=alert_group, author=user_1, resolution_note_slack_message=resolution_note_slack_message
    )

    cascading_objects = [
        user_1,
        user_2,
        team,
        user_notification_policy,
        schedule,
        custom_action,
        escalation_chain,
        escalation_policy,
        alert_receive_channel,
        channel_filter,
        alert_group,
        alert,
        alert_group_log_record,
        user_notification_policy_log_record,
        phone_call,
        sms,
        telegram_message,
        telegram_user_connector,
        telegram_channel,
        telegram_verification_code,
        telegram_channel_verification_code,
        slack_message,
        slack_action_record,
        plugin_token,
        public_api_token,
        invitation,
        resolution_note,
        resolution_note_slack_message,
    ]

    organization.delete()
    for obj in cascading_objects:
        with pytest.raises(ObjectDoesNotExist):
            obj.refresh_from_db()
