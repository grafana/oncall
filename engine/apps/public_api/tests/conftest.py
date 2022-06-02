import pytest
from django.utils import dateparse, timezone
from pytest_factoryboy import register

from apps.alerts.models import EscalationPolicy, ResolutionNote
from apps.auth_token.models import ApiAuthToken
from apps.base.models import UserNotificationPolicy
from apps.public_api import constants as public_api_constants
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleICal
from apps.user_management.tests.factories import OrganizationFactory, UserFactory
from common.constants.role import Role

register(UserFactory)
register(OrganizationFactory)


@pytest.fixture()
def make_organization_and_user_with_token(make_organization_and_user, make_public_api_token):
    def _make_organization_and_user_with_token():
        organization, user = make_organization_and_user()
        _, token = make_public_api_token(user, organization)
        return organization, user, token

    return _make_organization_and_user_with_token


@pytest.fixture()
def make_organization_and_user_with_slack_identities_for_demo_token(
    make_slack_team_identity,
    make_organization,
    make_slack_user_identity,
    make_user,
):
    def _make_organization_and_user_with_slack_identities_for_demo_token():
        slack_team_identity = make_slack_team_identity(slack_id=public_api_constants.DEMO_SLACK_TEAM_ID)
        organization = make_organization(
            slack_team_identity=slack_team_identity, public_primary_key=public_api_constants.DEMO_ORGANIZATION_ID
        )
        slack_user_identity = make_slack_user_identity(
            slack_id=public_api_constants.DEMO_SLACK_USER_ID,
            slack_team_identity=slack_team_identity,
        )
        user = make_user(
            organization=organization,
            public_primary_key=public_api_constants.DEMO_USER_ID,
            email=public_api_constants.DEMO_USER_EMAIL,
            username=public_api_constants.DEMO_USER_USERNAME,
            role=Role.ADMIN,
            slack_user_identity=slack_user_identity,
        )
        ApiAuthToken.create_auth_token(user, organization, public_api_constants.DEMO_AUTH_TOKEN)
        token = public_api_constants.DEMO_AUTH_TOKEN
        return organization, user, token

    return _make_organization_and_user_with_slack_identities_for_demo_token


@pytest.fixture()
def make_data_for_demo_token(
    make_alert_receive_channel,
    make_channel_filter,
    make_escalation_chain,
    make_escalation_policy,
    make_alert_group,
    make_alert,
    make_resolution_note,
    make_custom_action,
    make_slack_user_group,
    make_schedule,
    make_on_call_shift,
    make_slack_channel,
    make_user_notification_policy,
):
    def _make_data_for_demo_token(organization, user):
        alert_receive_channel = make_alert_receive_channel(
            organization,
            public_primary_key=public_api_constants.DEMO_INTEGRATION_ID,
            verbal_name=public_api_constants.DEMO_INTEGRATION_NAME,
        )
        route_1 = make_channel_filter(
            public_primary_key=public_api_constants.DEMO_ROUTE_ID_1,
            alert_receive_channel=alert_receive_channel,
            slack_channel_id=public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID,
            filtering_term="us-(east|west)",
            order=0,
        )
        make_channel_filter(
            public_primary_key=public_api_constants.DEMO_ROUTE_ID_2,
            alert_receive_channel=alert_receive_channel,
            slack_channel_id=public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID,
            filtering_term=".*",
            order=1,
            is_default=True,
        )
        escalation_chain = make_escalation_chain(
            organization, public_primary_key=public_api_constants.DEMO_ESCALATION_CHAIN_ID
        )
        make_escalation_policy(
            escalation_chain,
            public_primary_key=public_api_constants.DEMO_ESCALATION_POLICY_ID_1,
            escalation_policy_step=EscalationPolicy.STEP_WAIT,
            order=0,
            wait_delay=EscalationPolicy.ONE_MINUTE,
        )
        escalation_policy_2 = make_escalation_policy(
            escalation_chain,
            public_primary_key=public_api_constants.DEMO_ESCALATION_POLICY_ID_2,
            escalation_policy_step=EscalationPolicy.STEP_NOTIFY_USERS_QUEUE,
            order=1,
        )
        escalation_policy_2.notify_to_users_queue.add(user)
        alert_group = make_alert_group(
            alert_receive_channel,
            public_primary_key=public_api_constants.DEMO_INCIDENT_ID,
            resolved=True,
            channel_filter=route_1,
        )
        alert_group.started_at = dateparse.parse_datetime(public_api_constants.DEMO_INCIDENT_CREATED_AT)
        alert_group.resolved_at = dateparse.parse_datetime(public_api_constants.DEMO_INCIDENT_RESOLVED_AT)
        alert_group.save(update_fields=["started_at", "resolved_at"])
        for alert_id, created_at in public_api_constants.DEMO_ALERT_IDS:
            alert = make_alert(
                public_primary_key=alert_id,
                alert_group=alert_group,
                raw_request_data=public_api_constants.DEMO_ALERT_PAYLOAD,
            )
            alert.created_at = dateparse.parse_datetime(created_at)
            alert.save(update_fields=["created_at"])

        resolution_note = make_resolution_note(
            alert_group=alert_group,
            source=ResolutionNote.Source.WEB,
            author=user,
            public_primary_key=public_api_constants.DEMO_RESOLUTION_NOTE_ID,
            message_text=public_api_constants.DEMO_RESOLUTION_NOTE_TEXT,
        )
        resolution_note.created_at = dateparse.parse_datetime(public_api_constants.DEMO_RESOLUTION_NOTE_CREATED_AT)
        resolution_note.save(update_fields=["created_at"])

        make_custom_action(
            public_primary_key=public_api_constants.DEMO_CUSTOM_ACTION_ID,
            organization=organization,
            name=public_api_constants.DEMO_CUSTOM_ACTION_NAME,
        )

        user_group = make_slack_user_group(
            public_primary_key=public_api_constants.DEMO_SLACK_USER_GROUP_ID,
            name=public_api_constants.DEMO_SLACK_USER_GROUP_NAME,
            handle=public_api_constants.DEMO_SLACK_USER_GROUP_HANDLE,
            slack_id=public_api_constants.DEMO_SLACK_USER_GROUP_SLACK_ID,
            slack_team_identity=organization.slack_team_identity,
        )

        # ical schedule
        make_schedule(
            organization=organization,
            schedule_class=OnCallScheduleICal,
            public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_ICAL,
            ical_url_primary=public_api_constants.DEMO_SCHEDULE_ICAL_URL_PRIMARY,
            ical_url_overrides=public_api_constants.DEMO_SCHEDULE_ICAL_URL_OVERRIDES,
            name=public_api_constants.DEMO_SCHEDULE_NAME_ICAL,
            channel=public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
            user_group=user_group,
        )
        # calendar schedule
        schedule_calendar = make_schedule(
            organization=organization,
            schedule_class=OnCallScheduleCalendar,
            public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_CALENDAR,
            name=public_api_constants.DEMO_SCHEDULE_NAME_CALENDAR,
            channel=public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
            user_group=user_group,
            time_zone="America/New_york",
        )

        on_call_shift_1 = make_on_call_shift(
            shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT,
            organization=organization,
            public_primary_key=public_api_constants.DEMO_ON_CALL_SHIFT_ID_1,
            name=public_api_constants.DEMO_ON_CALL_SHIFT_NAME_1,
            start=dateparse.parse_datetime(public_api_constants.DEMO_ON_CALL_SHIFT_START_1),
            duration=timezone.timedelta(seconds=public_api_constants.DEMO_ON_CALL_SHIFT_DURATION),
        )
        on_call_shift_1.users.add(user)

        on_call_shift_2 = make_on_call_shift(
            shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT,
            organization=organization,
            public_primary_key=public_api_constants.DEMO_ON_CALL_SHIFT_ID_2,
            name=public_api_constants.DEMO_ON_CALL_SHIFT_NAME_2,
            start=dateparse.parse_datetime(public_api_constants.DEMO_ON_CALL_SHIFT_START_2),
            duration=timezone.timedelta(seconds=public_api_constants.DEMO_ON_CALL_SHIFT_DURATION),
            frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
            interval=2,
            by_day=public_api_constants.DEMO_ON_CALL_SHIFT_BY_DAY,
            source=CustomOnCallShift.SOURCE_TERRAFORM,
        )
        on_call_shift_2.users.add(user)

        schedule_calendar.custom_on_call_shifts.add(on_call_shift_1)
        schedule_calendar.custom_on_call_shifts.add(on_call_shift_2)

        make_slack_channel(
            organization.slack_team_identity,
            slack_id=public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
            name=public_api_constants.DEMO_SLACK_CHANNEL_NAME,
        )
        make_user_notification_policy(
            public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_1,
            important=False,
            user=user,
            notify_by=UserNotificationPolicy.NotificationChannel.SMS,
            step=UserNotificationPolicy.Step.NOTIFY,
            order=0,
        )
        make_user_notification_policy(
            public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_2,
            important=False,
            user=user,
            step=UserNotificationPolicy.Step.WAIT,
            wait_delay=UserNotificationPolicy.FIVE_MINUTES,
            order=1,
        )
        make_user_notification_policy(
            public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_3,
            important=False,
            user=user,
            step=UserNotificationPolicy.Step.NOTIFY,
            notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
            order=2,
        )

        make_user_notification_policy(
            public_primary_key=public_api_constants.DEMO_PERSONAL_NOTIFICATION_ID_4,
            important=True,
            user=user,
            step=UserNotificationPolicy.Step.NOTIFY,
            notify_by=UserNotificationPolicy.NotificationChannel.PHONE_CALL,
            order=0,
        )
        return

    return _make_data_for_demo_token
