import json
import sys
import uuid
from importlib import import_module, reload

import pytest
from django.db.models.signals import post_save
from django.urls import clear_url_caches
from pytest_factoryboy import register
from rest_framework.test import APIClient
from telegram import Bot

from apps.alerts.models import (
    Alert,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    MaintainableObject,
    ResolutionNote,
    listen_for_alert_model_save,
    listen_for_alertgrouplogrecord,
    listen_for_alertreceivechannel_model_save,
)
from apps.alerts.signals import user_notification_action_triggered_signal
from apps.alerts.tests.factories import (
    AlertFactory,
    AlertGroupFactory,
    AlertGroupLogRecordFactory,
    AlertReceiveChannelFactory,
    ChannelFilterFactory,
    CustomActionFactory,
    EscalationChainFactory,
    EscalationPolicyFactory,
    InvitationFactory,
    ResolutionNoteFactory,
    ResolutionNoteSlackMessageFactory,
)
from apps.auth_token.models import ApiAuthToken, PluginAuthToken
from apps.base.models.user_notification_policy_log_record import (
    UserNotificationPolicyLogRecord,
    listen_for_usernotificationpolicylogrecord_model_save,
)
from apps.base.tests.factories import (
    LiveSettingFactory,
    UserNotificationPolicyFactory,
    UserNotificationPolicyLogRecordFactory,
)
from apps.heartbeat.tests.factories import IntegrationHeartBeatFactory
from apps.schedules.tests.factories import (
    CustomOnCallShiftFactory,
    OnCallScheduleCalendarFactory,
    OnCallScheduleFactory,
    OnCallScheduleICalFactory,
)
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.tests.factories import (
    SlackActionRecordFactory,
    SlackChannelFactory,
    SlackMessageFactory,
    SlackTeamIdentityFactory,
    SlackUserGroupFactory,
    SlackUserIdentityFactory,
)
from apps.telegram.tests.factories import (
    TelegramChannelFactory,
    TelegramChannelVerificationCodeFactory,
    TelegramMessageFactory,
    TelegramToUserConnectorFactory,
    TelegramVerificationCodeFactory,
)
from apps.twilioapp.tests.factories import PhoneCallFactory, SMSFactory
from apps.user_management.models.user import User, listen_for_user_model_save
from apps.user_management.tests.factories import OrganizationFactory, TeamFactory, UserFactory
from common.constants.role import Role

register(OrganizationFactory)
register(UserFactory)
register(TeamFactory)


register(AlertReceiveChannelFactory)
register(ChannelFilterFactory)
register(EscalationPolicyFactory)
register(OnCallScheduleICalFactory)
register(OnCallScheduleCalendarFactory)
register(CustomOnCallShiftFactory)
register(AlertFactory)
register(AlertGroupFactory)
register(AlertGroupLogRecordFactory)
register(InvitationFactory)
register(CustomActionFactory)
register(SlackUserGroupFactory)

register(SlackUserIdentityFactory)
register(SlackTeamIdentityFactory)
register(SlackMessageFactory)
register(SlackActionRecordFactory)

register(TelegramToUserConnectorFactory)
register(TelegramChannelFactory)
register(TelegramVerificationCodeFactory)
register(TelegramChannelVerificationCodeFactory)
register(TelegramMessageFactory)

register(ResolutionNoteSlackMessageFactory)

register(PhoneCallFactory)
register(SMSFactory)
# register(EmailMessageFactory)

register(IntegrationHeartBeatFactory)

register(LiveSettingFactory)


@pytest.fixture(autouse=True)
def mock_slack_api_call(monkeypatch):
    def mock_api_call(*args, **kwargs):
        return {
            "status": 200,
            "usergroups": [],
            "channel": {"id": "TEST_CHANNEL_ID"},
            "user": {
                "name": "TEST_SLACK_LOGIN",
                "real_name": "TEST_SLACK_NAME",
                "profile": {"image_512": "TEST_SLACK_IMAGE"},
            },
            "team": {"name": "TEST_TEAM"},
        }

    monkeypatch.setattr(SlackClientWithErrorHandling, "api_call", mock_api_call)


@pytest.fixture(autouse=True)
def mock_telegram_bot_username(monkeypatch):
    def mock_username(*args, **kwargs):
        return "amixr_bot"

    monkeypatch.setattr(Bot, "username", mock_username)


@pytest.fixture
def make_organization():
    def _make_organization(**kwargs):
        organization = OrganizationFactory(**kwargs)

        return organization

    return _make_organization


@pytest.fixture
def make_user_for_organization():
    def _make_user_for_organization(organization, role=Role.ADMIN, **kwargs):
        post_save.disconnect(listen_for_user_model_save, sender=User)
        user = UserFactory(organization=organization, role=role, **kwargs)
        post_save.disconnect(listen_for_user_model_save, sender=User)
        return user

    return _make_user_for_organization


@pytest.fixture
def make_token_for_organization():
    def _make_token_for_organization(organization):
        return PluginAuthToken.create_auth_token(organization)

    return _make_token_for_organization


@pytest.fixture
def make_public_api_token():
    def _make_public_api_token(user, organization, name="test_api_token"):
        return ApiAuthToken.create_auth_token(user, organization, name)

    return _make_public_api_token


@pytest.fixture
def make_user_auth_headers():
    def _make_user_auth_headers(user, token):
        return {
            "HTTP_X-Instance-Context": json.dumps(
                {"stack_id": user.organization.stack_id, "org_id": user.organization.org_id}
            ),
            "HTTP_X-Grafana-Context": json.dumps({"UserId": user.user_id}),
            "HTTP_AUTHORIZATION": f"{token}",
        }

    return _make_user_auth_headers


@pytest.fixture
def make_user():
    def _make_user(role=Role.ADMIN, **kwargs):
        user = UserFactory(role=role, **kwargs)

        return user

    return _make_user


@pytest.fixture
def make_organization_and_user(make_organization, make_user_for_organization):
    def _make_organization_and_user(role=Role.ADMIN):
        organization = make_organization()
        user = make_user_for_organization(organization=organization, role=role)
        return organization, user

    return _make_organization_and_user


@pytest.fixture
def make_organization_and_user_with_slack_identities(
    make_organization_with_slack_team_identity, make_user_with_slack_user_identity
):
    def _make_organization_and_user_with_slack_identities(role=Role.ADMIN):
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        user, slack_user_identity = make_user_with_slack_user_identity(slack_team_identity, organization, role=role)

        return organization, user, slack_team_identity, slack_user_identity

    return _make_organization_and_user_with_slack_identities


@pytest.fixture
def make_user_with_slack_user_identity():
    def _make_slack_user_identity_with_user(slack_team_identity, organization, role=Role.ADMIN, **kwargs):
        slack_user_identity = SlackUserIdentityFactory(
            slack_team_identity=slack_team_identity,
            **kwargs,
        )
        user = UserFactory(slack_user_identity=slack_user_identity, organization=organization, role=role)
        return user, slack_user_identity

    return _make_slack_user_identity_with_user


@pytest.fixture
def make_organization_with_slack_team_identity(make_slack_team_identity):
    def _make_slack_team_identity_with_organization(**kwargs):
        slack_team_identity = make_slack_team_identity(**kwargs)
        organization = OrganizationFactory(slack_team_identity=slack_team_identity)
        return organization, slack_team_identity

    return _make_slack_team_identity_with_organization


@pytest.fixture
def make_slack_team_identity():
    def _make_slack_team_identity(**kwargs):
        slack_team_identity = SlackTeamIdentityFactory(**kwargs)
        return slack_team_identity

    return _make_slack_team_identity


@pytest.fixture
def make_slack_user_identity():
    def _make_slack_user_identity(**kwargs):
        slack_user_identity = SlackUserIdentityFactory(**kwargs)
        return slack_user_identity

    return _make_slack_user_identity


@pytest.fixture
def make_slack_message():
    def _make_slack_message(alert_group, **kwargs):
        organization = alert_group.channel.organization
        slack_message = SlackMessageFactory(
            alert_group=alert_group,
            organization=organization,
            _slack_team_identity=organization.slack_team_identity,
            **kwargs,
        )
        return slack_message

    return _make_slack_message


@pytest.fixture
def make_slack_action_record():
    def _make_slack_action_record(organization, user, **kwargs):
        return SlackActionRecordFactory(organization=organization, user=user, **kwargs)

    return _make_slack_action_record


@pytest.fixture
def client_with_user():
    def _client_with_user(user):
        """The client with logged in user"""

        client = APIClient()
        client.force_login(user)

        return client

    return _client_with_user


@pytest.fixture
def make_team():
    def _make_team(organization, **kwargs):
        team = TeamFactory(organization=organization, **kwargs)
        return team

    return _make_team


@pytest.fixture
def make_alert_receive_channel():
    def _make_alert_receive_channel(organization, **kwargs):
        if "integration" not in kwargs:
            kwargs["integration"] = AlertReceiveChannel.INTEGRATION_GRAFANA
        post_save.disconnect(listen_for_alertreceivechannel_model_save, sender=AlertReceiveChannel)
        alert_receive_channel = AlertReceiveChannelFactory(organization=organization, **kwargs)
        post_save.connect(listen_for_alertreceivechannel_model_save, sender=AlertReceiveChannel)
        return alert_receive_channel

    return _make_alert_receive_channel


@pytest.fixture
def make_channel_filter():
    def _make_channel_filter(alert_receive_channel, filtering_term=None, **kwargs):
        channel_filter = ChannelFilterFactory(
            filtering_term=filtering_term,
            alert_receive_channel=alert_receive_channel,
            **kwargs,
        )
        return channel_filter

    return _make_channel_filter


@pytest.fixture
def make_channel_filter_with_post_save():
    def _make_channel_filter(alert_receive_channel, filtering_term=None, **kwargs):
        channel_filter = ChannelFilterFactory(
            filtering_term=filtering_term,
            alert_receive_channel=alert_receive_channel,
            **kwargs,
        )
        return channel_filter

    return _make_channel_filter


@pytest.fixture
def make_escalation_chain():
    def _make_escalation_chain(organization, **kwargs):
        escalation_chain = EscalationChainFactory(organization=organization, **kwargs)
        return escalation_chain

    return _make_escalation_chain


@pytest.fixture
def make_escalation_policy():
    def _make_escalation_policy(escalation_chain, escalation_policy_step, **kwargs):
        escalation_policy = EscalationPolicyFactory(
            escalation_chain=escalation_chain, step=escalation_policy_step, **kwargs
        )
        return escalation_policy

    return _make_escalation_policy


@pytest.fixture
def make_user_notification_policy():
    def _make_user_notification_policy(user, step, **kwargs):
        user_notification_policy = UserNotificationPolicyFactory(user=user, step=step, **kwargs)
        return user_notification_policy

    return _make_user_notification_policy


@pytest.fixture
def make_user_notification_policy_log_record():
    def _make_user_notification_policy_log_record(**kwargs):
        post_save.disconnect(
            listen_for_usernotificationpolicylogrecord_model_save, sender=UserNotificationPolicyLogRecord
        )
        user_notification_policy_log_record = UserNotificationPolicyLogRecordFactory(**kwargs)
        post_save.connect(listen_for_usernotificationpolicylogrecord_model_save, sender=UserNotificationPolicyLogRecord)

        return user_notification_policy_log_record

    return _make_user_notification_policy_log_record


@pytest.fixture
def make_integration_escalation_chain_route_escalation_policy(
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
    make_escalation_policy,
):
    def _make_integration_escalation_chain_route_escalation_policy(organization, escalation_policy_step):
        alert_receive_channel = make_alert_receive_channel(organization)
        escalation_chain = make_escalation_chain(organization)
        default_channel_filter = make_channel_filter(
            alert_receive_channel, escalation_chain=escalation_chain, is_default=True
        )
        escalation_policy = make_escalation_policy(escalation_chain, escalation_policy_step)

        return alert_receive_channel, escalation_chain, default_channel_filter, escalation_policy

    return _make_integration_escalation_chain_route_escalation_policy


@pytest.fixture
def make_invitation():
    def _make_invitation(alert_group, author, invitee, **kwargs):
        invitation = InvitationFactory(alert_group=alert_group, author=author, invitee=invitee, **kwargs)
        return invitation

    return _make_invitation


@pytest.fixture
def make_schedule():
    def _make_schedule(organization, schedule_class, **kwargs):
        factory = OnCallScheduleFactory.get_factory_for_class(schedule_class)
        schedule = factory(organization=organization, **kwargs)
        return schedule

    return _make_schedule


@pytest.fixture
def make_on_call_shift():
    def _make_on_call_shift(organization, shift_type, **kwargs):
        on_call_shift = CustomOnCallShiftFactory(organization=organization, type=shift_type, **kwargs)
        return on_call_shift

    return _make_on_call_shift


@pytest.fixture
def make_alert_group():
    def _make_alert_group(alert_receive_channel, **kwargs):
        alert_group = AlertGroupFactory(channel=alert_receive_channel, **kwargs)
        return alert_group

    return _make_alert_group


@pytest.fixture
def make_alert_group_log_record():
    def _make_alert_group_log_record(alert_group, type, author, **kwargs):
        post_save.disconnect(listen_for_alertgrouplogrecord, sender=AlertGroupLogRecord)
        log_record = AlertGroupLogRecordFactory(alert_group=alert_group, type=type, author=author, **kwargs)
        post_save.connect(listen_for_alertgrouplogrecord, sender=AlertGroupLogRecord)
        return log_record

    return _make_alert_group_log_record


@pytest.fixture
def make_resolution_note():
    def _make_resolution_note(alert_group, source=ResolutionNote.Source.WEB, author=None, **kwargs):
        resolution_note = ResolutionNoteFactory(alert_group=alert_group, source=source, author=author, **kwargs)
        return resolution_note

    return _make_resolution_note


@pytest.fixture
def make_resolution_note_slack_message():
    def _make_resolution_note_slack_message(alert_group, user, added_by_user, **kwargs):
        return ResolutionNoteSlackMessageFactory(
            alert_group=alert_group, user=user, added_by_user=added_by_user, **kwargs
        )

    return _make_resolution_note_slack_message


@pytest.fixture
def make_alert():
    def _make_alert(alert_group, raw_request_data, **kwargs):
        post_save.disconnect(listen_for_alert_model_save, sender=Alert)
        alert = AlertFactory(group=alert_group, raw_request_data=raw_request_data, **kwargs)
        post_save.connect(listen_for_alert_model_save, sender=Alert)
        return alert

    return _make_alert


@pytest.fixture
def make_alert_with_custom_create_method():
    def _make_alert_with_custom_create_method(
        title,
        message,
        image_url,
        link_to_upstream_details,
        alert_receive_channel,
        integration_unique_data,
        raw_request_data,
        **kwargs,
    ):
        post_save.disconnect(listen_for_alert_model_save, sender=Alert)
        alert = Alert.create(
            title,
            message,
            image_url,
            link_to_upstream_details,
            alert_receive_channel,
            integration_unique_data,
            raw_request_data,
            **kwargs,
        )
        post_save.connect(listen_for_alert_model_save, sender=Alert)
        return alert

    return _make_alert_with_custom_create_method


@pytest.fixture
def make_custom_action():
    def _make_custom_action(organization, **kwargs):
        custom_action = CustomActionFactory(organization=organization, **kwargs)
        return custom_action

    return _make_custom_action


@pytest.fixture
def make_slack_user_group():
    def _make_slack_user_group(slack_team_identity, **kwargs):
        slack_user_group = SlackUserGroupFactory(slack_team_identity=slack_team_identity, **kwargs)
        return slack_user_group

    return _make_slack_user_group


@pytest.fixture
def make_slack_channel():
    def _make_slack_channel(slack_team_identity, **kwargs):
        schedule = SlackChannelFactory(slack_team_identity=slack_team_identity, **kwargs)
        return schedule

    return _make_slack_channel


@pytest.fixture()
def mock_start_disable_maintenance_task(monkeypatch):
    def mocked_start_disable_maintenance_task(*args, **kwargs):
        return uuid.uuid4()

    monkeypatch.setattr(MaintainableObject, "start_disable_maintenance_task", mocked_start_disable_maintenance_task)


@pytest.fixture()
def make_organization_and_user_with_plugin_token(make_organization_and_user, make_token_for_organization):
    def _make_organization_and_user_with_plugin_token(role=Role.ADMIN):
        organization, user = make_organization_and_user(role=role)
        _, token = make_token_for_organization(organization)

        return organization, user, token

    return _make_organization_and_user_with_plugin_token


@pytest.fixture()
def mock_send_user_notification_signal(monkeypatch):
    def mocked_send_signal(*args, **kwargs):
        return None

    monkeypatch.setattr(user_notification_action_triggered_signal, "send", mocked_send_signal)


@pytest.fixture()
def make_telegram_user_connector():
    def _make_telegram_user_connector(user, **kwargs):
        return TelegramToUserConnectorFactory(user=user, **kwargs)

    return _make_telegram_user_connector


@pytest.fixture()
def make_telegram_channel():
    def _make_telegram_channel(organization, is_default_channel=False):
        return TelegramChannelFactory(organization=organization, is_default_channel=is_default_channel)

    return _make_telegram_channel


@pytest.fixture()
def make_telegram_verification_code():
    def _make_telegram_verification_code(user, **kwargs):
        return TelegramVerificationCodeFactory(user=user, **kwargs)

    return _make_telegram_verification_code


@pytest.fixture()
def make_telegram_channel_verification_code():
    def _make_telegram_channel_verification_code(organization, author, **kwargs):
        return TelegramChannelVerificationCodeFactory(organization=organization, author=author, **kwargs)

    return _make_telegram_channel_verification_code


@pytest.fixture()
def make_telegram_message():
    def _make_telegram_message(alert_group, message_type, **kwargs):
        return TelegramMessageFactory(alert_group=alert_group, message_type=message_type, **kwargs)

    return _make_telegram_message


@pytest.fixture()
def make_phone_call():
    def _make_phone_call(receiver, status, **kwargs):
        return PhoneCallFactory(receiver=receiver, status=status, **kwargs)

    return _make_phone_call


@pytest.fixture()
def make_sms():
    def _make_sms(receiver, status, **kwargs):
        return SMSFactory(receiver=receiver, status=status, **kwargs)

    return _make_sms


# TODO: restore email notifications
# @pytest.fixture()
# def make_email_message():
#     def _make_email_message(receiver, status, **kwargs):
#         return EmailMessageFactory(receiver=receiver, status=status, **kwargs)
#
#     return _make_email_message


@pytest.fixture()
def make_live_setting():
    def _make_live_setting(name, **kwargs):
        return LiveSettingFactory(name=name, **kwargs)

    return _make_live_setting


@pytest.fixture()
def make_integration_heartbeat():
    def _make_integration_heartbeat(alert_receive_channel, timeout_seconds=60, last_heartbeat_time=None, **kwargs):
        return IntegrationHeartBeatFactory(
            alert_receive_channel=alert_receive_channel,
            timeout_seconds=timeout_seconds,
            last_heartbeat_time=last_heartbeat_time,
            **kwargs,
        )

    return _make_integration_heartbeat


@pytest.fixture()
def load_slack_urls(settings):
    clear_url_caches()
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = True
    urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        reload(sys.modules[urlconf])
    else:
        import_module(urlconf)
