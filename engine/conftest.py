import datetime
import json
import os
import sys
import typing
import uuid
from importlib import import_module, reload

import pytest
from celery import Task
from django.db.models.signals import post_save
from django.urls import clear_url_caches
from django.utils import timezone
from pytest_factoryboy import register
from rest_framework.test import APIClient
from telegram import Bot

from apps.alerts.models import (
    Alert,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    MaintainableObject,
    ResolutionNote,
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
from apps.api.permissions import (
    ACTION_PREFIX,
    GrafanaAPIPermission,
    LegacyAccessControlCompatiblePermission,
    LegacyAccessControlRole,
    RBACPermission,
)
from apps.auth_token.models import ApiAuthToken, PluginAuthToken, SlackAuthToken
from apps.base.models.user_notification_policy_log_record import (
    UserNotificationPolicyLogRecord,
    listen_for_usernotificationpolicylogrecord_model_save,
)
from apps.base.tests.factories import (
    LiveSettingFactory,
    UserNotificationPolicyFactory,
    UserNotificationPolicyLogRecordFactory,
)
from apps.email.tests.factories import EmailMessageFactory
from apps.heartbeat.tests.factories import IntegrationHeartBeatFactory
from apps.mobile_app.models import MobileAppAuthToken, MobileAppVerificationToken
from apps.phone_notifications.phone_backend import PhoneBackend
from apps.phone_notifications.tests.factories import PhoneCallRecordFactory, SMSRecordFactory
from apps.phone_notifications.tests.mock_phone_provider import MockPhoneProvider
from apps.schedules.models import OnCallScheduleWeb
from apps.schedules.tests.factories import (
    CustomOnCallShiftFactory,
    OnCallScheduleCalendarFactory,
    OnCallScheduleFactory,
    OnCallScheduleICalFactory,
    ShiftSwapRequestFactory,
)
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.tests.factories import (
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
from apps.user_management.models.user import User, listen_for_user_model_save
from apps.user_management.tests.factories import OrganizationFactory, RegionFactory, TeamFactory, UserFactory
from apps.webhooks.tests.factories import CustomWebhookFactory, WebhookResponseFactory

register(OrganizationFactory)
register(UserFactory)
register(TeamFactory)


register(AlertReceiveChannelFactory)
register(ChannelFilterFactory)
register(EscalationPolicyFactory)
register(OnCallScheduleICalFactory)
register(OnCallScheduleCalendarFactory)
register(CustomOnCallShiftFactory)
register(ShiftSwapRequestFactory)
register(AlertFactory)
register(AlertGroupFactory)
register(AlertGroupLogRecordFactory)
register(InvitationFactory)
register(CustomActionFactory)
register(SlackUserGroupFactory)

register(SlackUserIdentityFactory)
register(SlackTeamIdentityFactory)
register(SlackMessageFactory)

register(TelegramToUserConnectorFactory)
register(TelegramChannelFactory)
register(TelegramVerificationCodeFactory)
register(TelegramChannelVerificationCodeFactory)
register(TelegramMessageFactory)

register(ResolutionNoteSlackMessageFactory)

register(PhoneCallRecordFactory)
register(SMSRecordFactory)
register(EmailMessageFactory)

register(IntegrationHeartBeatFactory)
register(LiveSettingFactory)

IS_RBAC_ENABLED = os.getenv("ONCALL_TESTING_RBAC_ENABLED", "True") == "True"


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
        return "oncall_bot"

    monkeypatch.setattr(Bot, "username", mock_username)


@pytest.fixture(autouse=True)
def mock_phone_provider(monkeypatch):
    def mock_get_provider(*args, **kwargs):
        return MockPhoneProvider()

    monkeypatch.setattr(PhoneBackend, "_get_phone_provider", mock_get_provider)


@pytest.fixture(autouse=True)
def mock_apply_async(monkeypatch):
    def mock_apply_async(*args, **kwargs):
        return uuid.uuid4()

    monkeypatch.setattr(Task, "apply_async", mock_apply_async)


@pytest.fixture
def make_organization():
    def _make_organization(**kwargs):
        return OrganizationFactory(**kwargs, is_rbac_permissions_enabled=IS_RBAC_ENABLED)

    return _make_organization


@pytest.fixture
def make_user_for_organization(make_user):
    def _make_user_for_organization(organization, role: typing.Optional[LegacyAccessControlRole] = None, **kwargs):
        post_save.disconnect(listen_for_user_model_save, sender=User)
        user = make_user(organization=organization, role=role, **kwargs)
        post_save.disconnect(listen_for_user_model_save, sender=User)
        return user

    return _make_user_for_organization


@pytest.fixture
def make_token_for_organization():
    def _make_token_for_organization(organization):
        return PluginAuthToken.create_auth_token(organization)

    return _make_token_for_organization


@pytest.fixture
def make_mobile_app_verification_token_for_user():
    def _make_mobile_app_verification_token_for_user(user, organization):
        return MobileAppVerificationToken.create_auth_token(user, organization)

    return _make_mobile_app_verification_token_for_user


@pytest.fixture
def make_mobile_app_auth_token_for_user():
    def _make_mobile_app_auth_token_for_user(user, organization):
        return MobileAppAuthToken.create_auth_token(user, organization)

    return _make_mobile_app_auth_token_for_user


@pytest.fixture
def make_slack_token_for_user():
    def _make_slack_token_for_user(user):
        return SlackAuthToken.create_auth_token(organization=user.organization, user=user)

    return _make_slack_token_for_user


@pytest.fixture
def make_public_api_token():
    def _make_public_api_token(user, organization, name="test_api_token"):
        return ApiAuthToken.create_auth_token(user, organization, name)

    return _make_public_api_token


@pytest.fixture
def make_user_auth_headers():
    def _make_user_auth_headers(
        user,
        token,
        grafana_token: typing.Optional[str] = None,
        grafana_context_data: typing.Optional[typing.Dict] = None,
    ):
        instance_context_headers = {"stack_id": user.organization.stack_id, "org_id": user.organization.org_id}
        grafana_context_headers = {"UserId": user.user_id}
        if grafana_token is not None:
            instance_context_headers["grafana_token"] = grafana_token
        if grafana_context_data is not None:
            grafana_context_headers.update(grafana_context_data)

        return {
            "HTTP_X-Instance-Context": json.dumps(instance_context_headers),
            "HTTP_X-Grafana-Context": json.dumps(grafana_context_headers),
            "HTTP_AUTHORIZATION": f"{token}",
        }

    return _make_user_auth_headers


RoleMapping = typing.Dict[LegacyAccessControlRole, typing.List[LegacyAccessControlCompatiblePermission]]


def get_user_permission_role_mapping_from_frontend_plugin_json() -> RoleMapping:
    """
    This is used to take the RBAC permission -> basic role grants on the frontend
    and test that the RBAC grants work the same way against the backend in terms of authorization
    """

    class PluginJSONRoleDefinition(typing.TypedDict):
        permissions: typing.List[GrafanaAPIPermission]

    class PluginJSONRole(typing.TypedDict):
        role: PluginJSONRoleDefinition
        grants: typing.List[str]

    class PluginJSON(typing.TypedDict):
        roles: typing.List[PluginJSONRole]

    with open("../grafana-plugin/src/plugin.json") as fp:
        plugin_json: PluginJSON = json.load(fp)

    role_mapping: RoleMapping = {
        LegacyAccessControlRole.VIEWER: [],
        LegacyAccessControlRole.EDITOR: [],
        LegacyAccessControlRole.ADMIN: [],
    }

    all_permission_classes: typing.Dict[str, LegacyAccessControlCompatiblePermission] = {
        getattr(RBACPermission.Permissions, attr).value: getattr(RBACPermission.Permissions, attr)
        for attr in dir(RBACPermission.Permissions)
        if not attr.startswith("_")
    }

    # we just care about getting the basic role grants, everything else can be ignored
    for role in plugin_json["roles"]:
        if grants := role["grants"]:
            for permission in role["role"]["permissions"]:
                # only concerned with grafana-oncall-app specific grants
                # ignore things like plugins.app:access actions
                action = permission["action"]
                permission_class = None

                if action.startswith(ACTION_PREFIX):
                    permission_class = all_permission_classes[action]

                if permission_class:
                    for grant in grants:
                        try:
                            role = LegacyAccessControlRole[grant.upper()]
                            if role not in role_mapping[role]:
                                role_mapping[role].append(permission_class)
                        except KeyError:
                            # may come across grants like "Grafana Admin"
                            # which we can ignore
                            continue

    return role_mapping


ROLE_PERMISSION_MAPPING = get_user_permission_role_mapping_from_frontend_plugin_json()


@pytest.fixture
def make_user():
    def _make_user(role: typing.Optional[LegacyAccessControlRole] = None, **kwargs):
        role = LegacyAccessControlRole.ADMIN if role is None else role
        permissions = kwargs.pop("permissions", None)
        if permissions is None:
            permissions_to_grant = ROLE_PERMISSION_MAPPING[role] if IS_RBAC_ENABLED else []
            permissions = [GrafanaAPIPermission(action=perm.value) for perm in permissions_to_grant]
        return UserFactory(role=role, permissions=permissions, **kwargs)

    return _make_user


@pytest.fixture
def make_organization_and_user(make_organization, make_user_for_organization):
    def _make_organization_and_user(role: typing.Optional[LegacyAccessControlRole] = None):
        organization = make_organization()
        user = make_user_for_organization(organization=organization, role=role)
        return organization, user

    return _make_organization_and_user


@pytest.fixture
def make_organization_and_user_with_slack_identities(
    make_organization_with_slack_team_identity, make_user_with_slack_user_identity
):
    def _make_organization_and_user_with_slack_identities(role: typing.Optional[LegacyAccessControlRole] = None):
        organization, slack_team_identity = make_organization_with_slack_team_identity()
        user, slack_user_identity = make_user_with_slack_user_identity(slack_team_identity, organization, role=role)
        return organization, user, slack_team_identity, slack_user_identity

    return _make_organization_and_user_with_slack_identities


@pytest.fixture
def make_user_with_slack_user_identity(make_user):
    def _make_slack_user_identity_with_user(
        slack_team_identity, organization, role: typing.Optional[LegacyAccessControlRole] = None, **kwargs
    ):
        slack_user_identity = SlackUserIdentityFactory(slack_team_identity=slack_team_identity, **kwargs)
        user = make_user(slack_user_identity=slack_user_identity, organization=organization, role=role)
        return user, slack_user_identity

    return _make_slack_user_identity_with_user


@pytest.fixture
def make_organization_with_slack_team_identity(make_slack_team_identity, make_organization):
    def _make_slack_team_identity_with_organization(**kwargs):
        slack_team_identity = make_slack_team_identity(**kwargs)
        organization = make_organization(slack_team_identity=slack_team_identity)
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
    def _make_slack_message(alert_group=None, organization=None, **kwargs):
        organization = organization or alert_group.channel.organization
        slack_message = SlackMessageFactory(
            alert_group=alert_group,
            organization=organization,
            _slack_team_identity=organization.slack_team_identity,
            **kwargs,
        )
        return slack_message

    return _make_slack_message


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
def make_alert_receive_channel_with_post_save_signal():
    def _make_alert_receive_channel(organization, **kwargs):
        if "integration" not in kwargs:
            kwargs["integration"] = AlertReceiveChannel.INTEGRATION_GRAFANA
        alert_receive_channel = AlertReceiveChannelFactory(organization=organization, **kwargs)
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
        alert = AlertFactory(group=alert_group, raw_request_data=raw_request_data, **kwargs)
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
        return alert

    return _make_alert_with_custom_create_method


@pytest.fixture
def make_custom_action():
    def _make_custom_action(organization, **kwargs):
        custom_action = CustomActionFactory(organization=organization, **kwargs)
        return custom_action

    return _make_custom_action


@pytest.fixture
def make_custom_webhook():
    def _make_custom_webhook(organization, **kwargs):
        custom_webhook = CustomWebhookFactory(organization=organization, **kwargs)
        return custom_webhook

    return _make_custom_webhook


@pytest.fixture
def make_webhook_response():
    def _make_webhook_response(**kwargs):
        webhook_response = WebhookResponseFactory(**kwargs)
        return webhook_response

    return _make_webhook_response


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
    def _make_organization_and_user_with_plugin_token(role: typing.Optional[LegacyAccessControlRole] = None):
        organization, user = make_organization_and_user(role)
        _, token = make_token_for_organization(organization)
        return organization, user, token

    return _make_organization_and_user_with_plugin_token


@pytest.fixture()
def make_organization_and_user_with_mobile_app_verification_token(
    make_organization_and_user, make_mobile_app_verification_token_for_user
):
    def _make_organization_and_user_with_mobile_app_verification_token(
        role: typing.Optional[LegacyAccessControlRole] = None,
    ):
        organization, user = make_organization_and_user(role)
        _, token = make_mobile_app_verification_token_for_user(user, organization)
        return organization, user, token

    return _make_organization_and_user_with_mobile_app_verification_token


@pytest.fixture()
def make_organization_and_user_with_mobile_app_auth_token(
    make_organization_and_user, make_mobile_app_auth_token_for_user
):
    def _make_organization_and_user_with_mobile_app_auth_token(
        role: typing.Optional[LegacyAccessControlRole] = None,
    ):
        organization, user = make_organization_and_user(role)
        _, token = make_mobile_app_auth_token_for_user(user, organization)
        return organization, user, token

    return _make_organization_and_user_with_mobile_app_auth_token


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
def make_phone_call_record():
    def _make_phone_call_record(receiver, **kwargs):
        return PhoneCallRecordFactory(receiver=receiver, **kwargs)

    return _make_phone_call_record


@pytest.fixture()
def make_sms_record():
    def _make_sms_record(receiver, **kwargs):
        return SMSRecordFactory(receiver=receiver, **kwargs)

    return _make_sms_record


@pytest.fixture()
def make_email_message():
    def _make_email_message(receiver, **kwargs):
        return EmailMessageFactory(receiver=receiver, **kwargs)

    return _make_email_message


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


@pytest.fixture
def reload_urls(settings):
    """
    Reloads Django URLs, especially useful when testing conditionally registered URLs
    """

    def _reload_urls():
        clear_url_caches()
        urlconf = settings.ROOT_URLCONF
        if urlconf in sys.modules:
            reload(sys.modules[urlconf])
        else:
            import_module(urlconf)

    return _reload_urls


@pytest.fixture()
def load_slack_urls(settings, reload_urls):
    settings.FEATURE_SLACK_INTEGRATION_ENABLED = True
    reload_urls()


@pytest.fixture
def make_region():
    def _make_region(**kwargs):
        region = RegionFactory(**kwargs)
        return region

    return _make_region


@pytest.fixture
def make_organization_and_region(make_organization, make_region):
    def _make_organization_and_region():
        organization = make_organization()
        region = make_region()
        organization.migration_destination = region
        return organization, region

    return _make_organization_and_region


@pytest.fixture()
def make_organization_and_user_with_token(make_organization_and_user, make_public_api_token):
    def _make_organization_and_user_with_token():
        organization, user = make_organization_and_user()
        _, token = make_public_api_token(user, organization)
        return organization, user, token

    return _make_organization_and_user_with_token


@pytest.fixture
def make_shift_swap_request():
    def _make_shift_swap_request(schedule, beneficiary, **kwargs):
        return ShiftSwapRequestFactory(schedule=schedule, beneficiary=beneficiary, **kwargs)

    return _make_shift_swap_request


@pytest.fixture
def shift_swap_request_setup(
    make_schedule, make_organization_and_user, make_user_for_organization, make_shift_swap_request
):
    def _shift_swap_request_setup(**kwargs):
        organization, beneficiary = make_organization_and_user()
        benefactor = make_user_for_organization(organization)

        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        two_days_from_now = tomorrow + datetime.timedelta(days=1)

        ssr = make_shift_swap_request(schedule, beneficiary, swap_start=tomorrow, swap_end=two_days_from_now, **kwargs)

        return ssr, beneficiary, benefactor

    return _shift_swap_request_setup
