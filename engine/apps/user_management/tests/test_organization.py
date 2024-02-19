import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroupLogRecord, AlertReceiveChannel, EscalationPolicy
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.schedules.models import OnCallScheduleICal, OnCallScheduleWeb
from apps.telegram.models import TelegramMessage
from apps.user_management.models import Organization


@pytest.mark.django_db
def test_organization_soft_delete(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization, integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    )

    org_id = organization.id
    organization.delete()

    deleted_organization = Organization.objects_with_deleted.get(id=org_id)
    # check if org soft-deleted
    assert deleted_organization.deleted_at is not None

    # check if public api responds with 404
    client = APIClient()
    url = reverse("api-public:integrations-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == 404

    # check if alert receiver view responds with 403
    url = reverse("integrations:alertmanager", kwargs={"alert_channel_key": alert_receive_channel.token})
    data = {"a": "b"}
    response = client.post(url, data, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_organization_hard_delete(
    make_organization,
    make_user,
    make_team,
    make_slack_team_identity,
    make_slack_user_identity,
    make_slack_message,
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
    make_sms_record,
    make_phone_call_record,
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

    # Creating different types of schedules to check that deletion works well with PolymorphicModel
    schedule_web = make_schedule(organization=organization, schedule_class=OnCallScheduleWeb)
    schedule_ical = make_schedule(organization=organization, schedule_class=OnCallScheduleICal)

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

    sms_record = make_sms_record(receiver=user_1, represents_alert=alert, represents_alert_group=alert_group)

    phone_call_record = make_phone_call_record(
        receiver=user_1, represents_alert=alert, represents_alert_group=alert_group
    )

    telegram_user_connector = make_telegram_user_connector(user=user_1)
    telegram_channel = make_telegram_channel(organization=organization)
    telegram_verification_code = make_telegram_verification_code(user=user_1)
    telegram_channel_verification_code = make_telegram_channel_verification_code(
        organization=organization, author=user_1
    )
    telegram_message = make_telegram_message(alert_group=alert_group, message_type=TelegramMessage.ALERT_GROUP_MESSAGE)

    slack_message = make_slack_message(alert_group=alert_group)

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
        schedule_web,
        schedule_ical,
        custom_action,
        escalation_chain,
        escalation_policy,
        alert_receive_channel,
        channel_filter,
        alert_group,
        alert,
        alert_group_log_record,
        user_notification_policy_log_record,
        phone_call_record,
        sms_record,
        telegram_message,
        telegram_user_connector,
        telegram_channel,
        telegram_verification_code,
        telegram_channel_verification_code,
        slack_message,
        plugin_token,
        public_api_token,
        invitation,
        resolution_note,
        resolution_note_slack_message,
    ]

    organization.hard_delete()
    for obj in cascading_objects:
        with pytest.raises(ObjectDoesNotExist):
            obj.refresh_from_db()


@pytest.mark.django_db
def test_get_notifiable_direct_paging_integrations(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_slack_team_identity,
    make_telegram_channel,
):
    def _make_org_and_arc(**arc_kwargs):
        org = make_organization()
        arc = make_alert_receive_channel(org, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, **arc_kwargs)
        return org, arc

    def _assert(org, arc, should_be_returned=True):
        notifiable_direct_paging_integrations = org.get_notifiable_direct_paging_integrations()
        if should_be_returned:
            assert arc in notifiable_direct_paging_integrations
        else:
            assert arc not in notifiable_direct_paging_integrations
        return notifiable_direct_paging_integrations

    # integration has no default channel filter
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=False)
    _assert(org, arc, should_be_returned=False)

    # integration has more than one channel filter
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=False)
    make_channel_filter(arc, is_default=False)
    _assert(org, arc)

    # integration's default channel filter is setup to notify via slack but Slack is not configured for the org
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=True, notify_in_slack=True)
    _assert(org, arc, should_be_returned=False)

    # integration's default channel filter is setup to notify via slack and Slack is configured for the org
    org, arc = _make_org_and_arc()
    slack_team_identity = make_slack_team_identity()
    org.slack_team_identity = slack_team_identity
    org.save()

    make_channel_filter(arc, is_default=True, notify_in_slack=True)
    _assert(org, arc)

    # integration's default channel filter is setup to notify via telegram but Telegram is not configured for the org
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=True, notify_in_slack=False, notify_in_telegram=True)
    _assert(org, arc, should_be_returned=False)

    # integration's default channel filter is setup to notify via telegram and Telegram is configured for the org
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=True, notify_in_slack=False, notify_in_telegram=True)
    make_telegram_channel(org)
    _assert(org, arc)

    # integration's default channel filter is contactable via a custom messaging backend
    org, arc = _make_org_and_arc()
    make_channel_filter(
        arc,
        is_default=True,
        notify_in_slack=False,
        notification_backends={"MSTEAMS": {"channel": "test", "enabled": True}},
    )
    _assert(org, arc)

    # integration's default channel filter has an escalation chain attached to it
    org, arc = _make_org_and_arc()
    escalation_chain = make_escalation_chain(org)
    make_channel_filter(arc, is_default=True, notify_in_slack=False, escalation_chain=escalation_chain)
    _assert(org, arc)

    # integration has more than one channel filter associated with it, nevertheless the integration should only
    # be returned once
    org, arc = _make_org_and_arc()
    make_channel_filter(arc, is_default=True)
    make_channel_filter(arc, is_default=False)
    notifiable_direct_paging_integrations = _assert(org, arc)
    assert notifiable_direct_paging_integrations.count() == 1
