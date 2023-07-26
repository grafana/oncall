import json
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroup
from apps.alerts.paging import DirectPagingAlertGroupResolvedError
from apps.base.models import UserNotificationPolicy
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.slack.scenarios.manage_responders import (
    ALERT_GROUP_DATA_KEY,
    DIRECT_PAGING_SCHEDULE_SELECT_ID,
    DIRECT_PAGING_USER_SELECT_ID,
    USER_DATA_KEY,
    ManageRespondersRemoveUser,
    ManageRespondersScheduleChange,
    ManageRespondersUserChange,
    StartManageResponders,
)
from apps.slack.scenarios.paging import _get_schedules_select, _get_users_select

ORGANIZATION_ID = 12
ALERT_GROUP_ID = 42
TRIGGER_ID = "111"
CHANNEL_ID = "123"
MESSAGE_TS = "67"


def make_slack_payload(
    user=None,
    schedule=None,
    actions=None,
):
    payload = {
        "trigger_id": TRIGGER_ID,
        "view": {
            "id": "view-id",
            "private_metadata": json.dumps({"input_id_prefix": "", ALERT_GROUP_DATA_KEY: ALERT_GROUP_ID}),
            "state": {
                "values": {
                    DIRECT_PAGING_USER_SELECT_ID: {
                        ManageRespondersUserChange.routing_uid(): {
                            "selected_option": {"value": user.pk} if user else None
                        }
                    },
                    DIRECT_PAGING_SCHEDULE_SELECT_ID: {
                        ManageRespondersScheduleChange.routing_uid(): {
                            "selected_option": {"value": schedule.pk} if schedule else None
                        }
                    },
                }
            },
        },
    }
    if actions is not None:
        payload["actions"] = actions
    return payload


@pytest.fixture
def manage_responders_setup(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity, slack_id=CHANNEL_ID)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=MESSAGE_TS)
    slack_message.get_alert_group()  # fix FKs

    return organization, user, slack_team_identity, slack_user_identity


@pytest.mark.django_db
def test_initial_state(manage_responders_setup):
    payload = {
        "trigger_id": TRIGGER_ID,
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": ORGANIZATION_ID, "alert_group_pk": ALERT_GROUP_ID}),
            }
        ],
    }

    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup

    step = StartManageResponders(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[ALERT_GROUP_DATA_KEY] == ALERT_GROUP_ID


@pytest.mark.django_db
def test_add_user_no_warning(manage_responders_setup, make_schedule, make_on_call_shift, make_user_notification_policy):
    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup

    # set up schedule: user is on call
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        team=None,
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(hours=23, minutes=59, seconds=59),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    # setup notification policy
    make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.SMS,
    )

    payload = make_slack_payload(user=user)

    step = ManageRespondersUserChange(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)

    # check there's a delete button for the user
    assert mock_slack_api_call.call_args.kwargs["view"]["blocks"][0]["accessory"]["value"] == str(user.pk)


@pytest.mark.django_db
def test_add_user_raise_warning(manage_responders_setup):
    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup
    # user is not on call
    payload = make_slack_payload(user=user)

    step = ManageRespondersUserChange(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.push",)
    assert mock_slack_api_call.call_args.kwargs["view"]["callback_id"] == "ManageRespondersConfirmUserChange"
    text_from_blocks = "".join(
        b["text"]["text"] for b in mock_slack_api_call.call_args.kwargs["view"]["blocks"] if b["type"] == "section"
    )
    assert f"*{user.username}* is not on-call" in text_from_blocks
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[USER_DATA_KEY] == user.pk


@pytest.mark.django_db
def test_add_schedule(manage_responders_setup, make_schedule, make_on_call_shift):
    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(hours=23, minutes=59, seconds=59),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    payload = make_slack_payload(schedule=schedule)

    step = ManageRespondersScheduleChange(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    assert mock_slack_api_call.call_args.kwargs["view"]["blocks"][0]["accessory"]["value"] == str(user.pk)


@pytest.mark.django_db
def test_add_schedule_alert_group_resolved(
    manage_responders_setup, make_schedule, make_on_call_shift, make_user_notification_policy
):
    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup
    AlertGroup.objects.filter(pk=ALERT_GROUP_ID).update(resolved=True)  # resolve alert group

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(hours=23, minutes=59, seconds=59),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    payload = make_slack_payload(schedule=schedule)

    step = ManageRespondersScheduleChange(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    assert (
        DirectPagingAlertGroupResolvedError.DETAIL
        in mock_slack_api_call.call_args.kwargs["view"]["blocks"][0]["text"]["text"]
    )


@pytest.mark.django_db
def test_remove_user(manage_responders_setup):
    organization, user, slack_team_identity, slack_user_identity = manage_responders_setup

    payload = make_slack_payload(actions=[{"value": user.pk}])
    step = ManageRespondersRemoveUser(slack_team_identity, organization, user)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    # check there's no list of users in the view
    assert mock_slack_api_call.call_args.kwargs["view"]["blocks"][0]["accessory"]["type"] != "button"


@pytest.mark.django_db
def test_get_users_select(make_organization, make_user):
    organization = make_organization()
    for _ in range(3):
        make_user(organization=organization)

    select_options = _get_users_select(organization=organization, input_id_prefix="test", action_id="test")
    assert len(select_options["accessory"]["options"]) == 3
    assert "option_groups" not in select_options["accessory"]

    select_option_groups = _get_users_select(
        organization=organization, input_id_prefix="test", action_id="test", max_options_per_group=2
    )
    assert len(select_option_groups["accessory"]["option_groups"]) == 2
    assert len(select_option_groups["accessory"]["option_groups"][0]["options"]) == 2
    assert len(select_option_groups["accessory"]["option_groups"][1]["options"]) == 1
    assert "options" not in select_option_groups["accessory"]


@pytest.mark.django_db
def test_get_schedules_select(make_organization, make_schedule):
    organization = make_organization()
    for _ in range(3):
        make_schedule(organization, schedule_class=OnCallScheduleWeb)

    select_options = _get_schedules_select(organization=organization, input_id_prefix="test", action_id="test")
    assert len(select_options["accessory"]["options"]) == 3
    assert "option_groups" not in select_options["accessory"]

    select_option_groups = _get_schedules_select(
        organization=organization, input_id_prefix="test", action_id="test", max_options_per_group=2
    )
    assert len(select_option_groups["accessory"]["option_groups"]) == 2
    assert len(select_option_groups["accessory"]["option_groups"][0]["options"]) == 2
    assert len(select_option_groups["accessory"]["option_groups"][1]["options"]) == 1
    assert "options" not in select_option_groups["accessory"]
