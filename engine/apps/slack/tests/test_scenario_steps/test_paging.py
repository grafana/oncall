import json
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.base.models import UserNotificationPolicy
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.slack.scenarios.paging import (
    DIRECT_PAGING_ADDITIONAL_RESPONDERS_INPUT_ID,
    DIRECT_PAGING_MESSAGE_INPUT_ID,
    DIRECT_PAGING_ORG_SELECT_ID,
    DIRECT_PAGING_SCHEDULE_SELECT_ID,
    DIRECT_PAGING_TEAM_SELECT_ID,
    DIRECT_PAGING_TITLE_INPUT_ID,
    DIRECT_PAGING_USER_SELECT_ID,
    DataKey,
    FinishDirectPaging,
    OnPagingCheckAdditionalResponders,
    OnPagingItemActionChange,
    OnPagingOrgChange,
    OnPagingScheduleChange,
    OnPagingTeamChange,
    OnPagingUserChange,
    Policy,
    StartDirectPaging,
    _get_organization_select,
)
from apps.user_management.models import Organization


def make_slack_payload(
    organization,
    team=None,
    user=None,
    schedule=None,
    additional_responders=False,
    current_users=None,
    current_schedules=None,
    actions=None,
):
    payload = {
        "channel_id": "123",
        "trigger_id": "111",
        "view": {
            "id": "view-id",
            "private_metadata": json.dumps(
                {
                    "input_id_prefix": "",
                    "channel_id": "123",
                    "submit_routing_uid": "FinishStepUID",
                    DataKey.USERS: current_users or {},
                    DataKey.SCHEDULES: current_schedules or {},
                }
            ),
            "state": {
                "values": {
                    DIRECT_PAGING_ORG_SELECT_ID: {
                        OnPagingOrgChange.routing_uid(): {"selected_option": {"value": organization.pk}}
                    },
                    DIRECT_PAGING_TEAM_SELECT_ID: {
                        OnPagingTeamChange.routing_uid(): {"selected_option": {"value": team.pk if team else None}}
                    },
                    DIRECT_PAGING_ADDITIONAL_RESPONDERS_INPUT_ID: {
                        OnPagingCheckAdditionalResponders.routing_uid(): {
                            "selected_options": ["something"] if additional_responders else []
                        }
                    },
                    DIRECT_PAGING_USER_SELECT_ID: {
                        OnPagingUserChange.routing_uid(): {"selected_option": {"value": user.pk} if user else None}
                    },
                    DIRECT_PAGING_SCHEDULE_SELECT_ID: {
                        OnPagingScheduleChange.routing_uid(): {
                            "selected_option": {"value": schedule.pk} if schedule else None
                        }
                    },
                    DIRECT_PAGING_TITLE_INPUT_ID: {FinishDirectPaging.routing_uid(): {"value": "The Title"}},
                    DIRECT_PAGING_MESSAGE_INPUT_ID: {FinishDirectPaging.routing_uid(): {"value": "The Message"}},
                }
            },
        },
    }
    if actions is not None:
        payload["actions"] = actions
    return payload


@pytest.mark.django_db
def test_initial_state(
    make_organization_and_user_with_slack_identities,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = {"channel_id": "123", "trigger_id": "111"}

    step = StartDirectPaging(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}
    assert metadata[DataKey.SCHEDULES] == {}


@pytest.mark.django_db
def test_add_user_no_warning(
    make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift, make_user_notification_policy
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
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

    payload = make_slack_payload(organization=organization, user=user)

    step = OnPagingUserChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.DEFAULT}


@pytest.mark.django_db
def test_add_user_maximum_exceeded(
    make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift, make_user_notification_policy
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
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

    payload = make_slack_payload(organization=organization, user=user)

    step = OnPagingUserChange(slack_team_identity)
    with patch("apps.slack.scenarios.paging.PRIVATE_METADATA_MAX_LENGTH", 100):
        with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    view_data = mock_slack_api_call.call_args.kwargs["view"]
    metadata = json.loads(view_data["private_metadata"])
    # metadata unchanged, ignoring the prefix
    original_metadata = json.loads(payload["view"]["private_metadata"])
    metadata.pop("input_id_prefix")
    original_metadata.pop("input_id_prefix")
    assert metadata == original_metadata
    # error message is displayed
    error_block = {
        "type": "section",
        "block_id": "error_message",
        "text": {"type": "mrkdwn", "text": ":warning: Cannot add user, maximum responders exceeded"},
    }
    assert error_block in view_data["blocks"]


@pytest.mark.django_db
def test_add_user_raise_warning(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    # user is not on call
    payload = make_slack_payload(organization=organization, user=user)

    step = OnPagingUserChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.push",)
    assert mock_slack_api_call.call_args.kwargs["view"]["callback_id"] == "OnPagingConfirmUserChange"
    text_from_blocks = "".join(
        b["text"]["text"] for b in mock_slack_api_call.call_args.kwargs["view"]["blocks"] if b["type"] == "section"
    )
    assert f"*{user.username}* is not on-call" in text_from_blocks
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}


@pytest.mark.django_db
def test_change_user_policy(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization,
        actions=[{"selected_option": {"value": f"{Policy.IMPORTANT}|{DataKey.USERS}|{user.pk}"}}],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.IMPORTANT}


@pytest.mark.django_db
def test_remove_user(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization,
        actions=[{"selected_option": {"value": f"{Policy.REMOVE_ACTION}|{DataKey.USERS}|{user.pk}"}}],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}


@pytest.mark.django_db
def test_trigger_paging_no_responders(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(organization=organization)

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_direct_paging.called_with(organization, None, user, "The Title", "The Message")


@pytest.mark.django_db
def test_trigger_paging(make_organization_and_user_with_slack_identities, make_team, make_schedule):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)
    payload = make_slack_payload(
        organization=organization,
        team=team,
        additional_responders=False,
    )

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_direct_paging.called_with(organization, team, user, "The Title", "The Message", [], [], None)


@pytest.mark.django_db
def test_trigger_paging_additional_responders(
    make_organization_and_user_with_slack_identities, make_team, make_schedule
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    payload = make_slack_payload(
        organization=organization,
        team=team,
        additional_responders=True,
        current_users={str(user.pk): Policy.IMPORTANT},
        current_schedules={str(schedule.pk): Policy.DEFAULT},
    )

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_direct_paging.called_with(
        organization, team, user, "The Title", "The Message", [(user, True)], [(schedule, False)], None
    )


@pytest.mark.django_db
def test_add_schedule(make_organization_and_user_with_slack_identities, make_schedule):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    payload = make_slack_payload(
        organization=organization,
        schedule=schedule,
        current_users={str(user.pk): Policy.IMPORTANT},
    )

    step = OnPagingScheduleChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.SCHEDULES] == {str(schedule.pk): Policy.DEFAULT}
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.IMPORTANT}


@pytest.mark.django_db
def test_add_schedule_responders_exceeded(make_organization_and_user_with_slack_identities, make_schedule):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    payload = make_slack_payload(
        organization=organization,
        schedule=schedule,
        current_users={str(user.pk): Policy.IMPORTANT},
    )

    step = OnPagingScheduleChange(slack_team_identity)
    with patch("apps.slack.scenarios.paging.PRIVATE_METADATA_MAX_LENGTH", 100):
        with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    view_data = mock_slack_api_call.call_args.kwargs["view"]
    metadata = json.loads(view_data["private_metadata"])
    # metadata unchanged, ignoring the prefix
    original_metadata = json.loads(payload["view"]["private_metadata"])
    metadata.pop("input_id_prefix")
    original_metadata.pop("input_id_prefix")
    assert metadata == original_metadata
    # error message is displayed
    error_block = {
        "type": "section",
        "block_id": "error_message",
        "text": {"type": "mrkdwn", "text": ":warning: Cannot add schedule, maximum responders exceeded"},
    }
    assert error_block in view_data["blocks"]


@pytest.mark.django_db
def test_change_schedule_policy(make_organization_and_user_with_slack_identities, make_schedule):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    payload = make_slack_payload(
        organization=organization,
        current_users={str(user.pk): Policy.DEFAULT},
        actions=[{"selected_option": {"value": f"{Policy.IMPORTANT}|{DataKey.SCHEDULES}|{schedule.pk}"}}],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.SCHEDULES] == {str(schedule.pk): Policy.IMPORTANT}
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.DEFAULT}


@pytest.mark.django_db
def test_remove_schedule(make_organization_and_user_with_slack_identities, make_schedule):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=None)
    payload = make_slack_payload(
        organization=organization,
        current_users={str(user.pk): Policy.DEFAULT},
        actions=[{"selected_option": {"value": f"{Policy.REMOVE_ACTION}|{DataKey.SCHEDULES}|{schedule.pk}"}}],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.SCHEDULES] == {}
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.DEFAULT}


@pytest.mark.django_db
def test_get_organization_select(make_organization):
    organization = make_organization(org_title="Organization", stack_slug="stack_slug")
    select = _get_organization_select(Organization.objects.filter(pk=organization.pk), organization, "test")

    assert len(select["element"]["options"]) == 1
    assert select["element"]["options"][0]["value"] == str(organization.pk)
    assert select["element"]["options"][0]["text"]["text"] == "Organization (stack_slug)"
