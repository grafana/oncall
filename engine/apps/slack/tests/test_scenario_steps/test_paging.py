import json
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.base.models import UserNotificationPolicy
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.slack.scenarios.paging import (
    DEFAULT_POLICY,
    DIRECT_PAGING_MESSAGE_INPUT_ID,
    DIRECT_PAGING_ORG_SELECT_ID,
    DIRECT_PAGING_TEAM_SELECT_ID,
    DIRECT_PAGING_TITLE_INPUT_ID,
    DIRECT_PAGING_USER_SELECT_ID,
    IMPORTANT_POLICY,
    REMOVE_ACTION,
    FinishDirectPaging,
    OnOrgChange,
    OnTeamChange,
    OnUserActionChange,
    OnUserChange,
    StartDirectPaging,
)


def make_slack_payload(organization, user=None, current_users=None, actions=None):
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
                    "current_users": current_users or {},
                }
            ),
            "state": {
                "values": {
                    DIRECT_PAGING_ORG_SELECT_ID: {
                        OnOrgChange.routing_uid(): {"selected_option": {"value": organization.pk}}
                    },
                    DIRECT_PAGING_TEAM_SELECT_ID: {OnTeamChange.routing_uid(): {"selected_option": {"value": 0}}},
                    DIRECT_PAGING_USER_SELECT_ID: {
                        OnUserChange.routing_uid(): {"selected_option": {"value": user.pk} if user else None}
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
def test_initial_users(
    make_organization_and_user_with_slack_identities,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = {"channel_id": "123", "trigger_id": "111"}

    step = StartDirectPaging(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata["current_users"] == {}


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

    step = OnUserChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata["current_users"] == {str(user.pk): DEFAULT_POLICY}


@pytest.mark.django_db
def test_add_user_raise_warning(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    # user is not on call
    payload = make_slack_payload(organization=organization, user=user)

    step = OnUserChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.push",)
    assert mock_slack_api_call.call_args.kwargs["view"]["callback_id"] == "OnConfirmUserChange"
    text_from_blocks = "".join(
        b["text"]["text"] for b in mock_slack_api_call.call_args.kwargs["view"]["blocks"] if b["type"] == "section"
    )
    assert f"*{user.username}* is not on-call" in text_from_blocks
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata["current_users"] == {}


@pytest.mark.django_db
def test_change_user_policy(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization, actions=[{"selected_option": {"value": f"{IMPORTANT_POLICY}|{user.pk}"}}]
    )

    step = OnUserActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata["current_users"] == {str(user.pk): IMPORTANT_POLICY}


@pytest.mark.django_db
def test_remove_user(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization, actions=[{"selected_option": {"value": f"{REMOVE_ACTION}|{user.pk}"}}]
    )

    step = OnUserActionChange(slack_team_identity)
    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.update",)
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata["current_users"] == {}


@pytest.mark.django_db
def test_trigger_paging(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(organization=organization, current_users={str(user.pk): IMPORTANT_POLICY})

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_direct_paging.called_with(organization, None, user, "The Title", "The Message", [(user, True)])
