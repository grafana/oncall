import json
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.slack.chatops_proxy_routing import make_private_metadata, make_value
from apps.slack.scenarios.paging import (
    DIRECT_PAGING_MESSAGE_INPUT_ID,
    DIRECT_PAGING_ORG_SELECT_ID,
    DIRECT_PAGING_TEAM_SELECT_ID,
    DIRECT_PAGING_USER_SELECT_ID,
    DataKey,
    FinishDirectPaging,
    OnPagingItemActionChange,
    OnPagingOrgChange,
    OnPagingTeamChange,
    OnPagingUserChange,
    Policy,
    StartDirectPaging,
    _get_organization_select,
    _get_team_select_blocks,
)
from apps.user_management.models import Organization


def make_slack_payload(organization, team=None, user=None, current_users=None, actions=None):
    payload = {
        "channel_id": "123",
        "trigger_id": "111",
        "view": {
            "id": "view-id",
            "private_metadata": make_private_metadata(
                {
                    "input_id_prefix": "",
                    "channel_id": "123",
                    "submit_routing_uid": "FinishStepUID",
                    DataKey.USERS: current_users or {},
                },
                organization,
            ),
            "state": {
                "values": {
                    DIRECT_PAGING_ORG_SELECT_ID: {
                        OnPagingOrgChange.routing_uid(): {
                            "selected_option": {"value": make_value({"id": organization.pk}, organization)}
                        }
                    },
                    DIRECT_PAGING_TEAM_SELECT_ID: {
                        OnPagingTeamChange.routing_uid(): {
                            "selected_option": {"value": make_value({"id": team.pk if team else None}, organization)}
                        }
                    },
                    DIRECT_PAGING_USER_SELECT_ID: {
                        OnPagingUserChange.routing_uid(): {
                            "selected_option": {"value": make_value({"id": user.pk}, organization)} if user else None
                        }
                    },
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
    _, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = {"channel_id": "123", "trigger_id": "111"}

    step = StartDirectPaging(slack_team_identity, user=user)
    with patch.object(step._slack_client, "views_open") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}


@pytest.mark.parametrize("role", (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.NONE))
@pytest.mark.django_db
def test_initial_unauthorized(make_organization_and_user_with_slack_identities, role):
    _, _, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities(role=role)
    payload = {"channel_id": "123", "trigger_id": "111"}

    step = StartDirectPaging(slack_team_identity)
    with patch.object(step._slack_client, "views_open") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    view = mock_slack_api_call.call_args.kwargs["view"]
    assert (
        view["blocks"][0]["text"]["text"]
        == ":warning: You do not have permission to perform this action.\nAsk an admin to upgrade your permissions."
    )


@pytest.mark.django_db
def test_add_user_no_warning(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
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

    payload = make_slack_payload(organization=organization, user=user)

    step = OnPagingUserChange(slack_team_identity)
    with patch.object(step._slack_client, "views_update") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.DEFAULT}


@pytest.mark.django_db
def test_add_user_maximum_exceeded(make_organization_and_user_with_slack_identities, make_schedule, make_on_call_shift):
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

    payload = make_slack_payload(organization=organization, user=user)

    step = OnPagingUserChange(slack_team_identity)
    with patch("apps.slack.scenarios.paging.PRIVATE_METADATA_MAX_LENGTH", 100):
        with patch.object(step._slack_client, "views_update") as mock_slack_api_call:
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

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
    with patch.object(step._slack_client, "views_push") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.kwargs["view"]["callback_id"] == "OnPagingConfirmUserChange"
    text_from_blocks = "".join(
        b["text"]["text"] for b in mock_slack_api_call.call_args.kwargs["view"]["blocks"] if b["type"] == "section"
    )
    assert (
        "This user is not currently on-call. We don't recommend to page users outside on-call hours."
        in text_from_blocks
    )
    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}


@pytest.mark.django_db
def test_change_user_policy(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization,
        actions=[
            {
                "selected_option": {
                    "value": make_value({"action": Policy.IMPORTANT, "key": DataKey.USERS, "id": user.pk}, organization)
                }
            }
        ],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "views_update") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {str(user.pk): Policy.IMPORTANT}


@pytest.mark.django_db
def test_remove_user(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(
        organization=organization,
        actions=[
            {
                "selected_option": {
                    "value": make_value(
                        {"action": Policy.REMOVE_ACTION, "key": DataKey.USERS, "id": user.pk}, organization
                    )
                }
            }
        ],
    )

    step = OnPagingItemActionChange(slack_team_identity)
    with patch.object(step._slack_client, "views_update") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    metadata = json.loads(mock_slack_api_call.call_args.kwargs["view"]["private_metadata"])
    assert metadata[DataKey.USERS] == {}


@pytest.mark.django_db
def test_trigger_paging_no_team_or_user_selected(make_organization_and_user_with_slack_identities):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    payload = make_slack_payload(organization=organization)

    step = FinishDirectPaging(slack_team_identity, user=user)

    with patch.object(step._slack_client, "api_call"):
        response = step.process_scenario(slack_user_identity, slack_team_identity, payload)

    response = response.data

    assert response["response_action"] == "update"
    assert (
        response["view"]["blocks"][0]["text"]["text"]
        == ":warning: At least one team or one user must be selected to directly page"
    )


@pytest.mark.parametrize("role", (LegacyAccessControlRole.VIEWER, LegacyAccessControlRole.NONE))
@pytest.mark.django_db
def test_trigger_paging_unauthorized(make_organization_and_user_with_slack_identities, role):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities(
        role=role
    )
    payload = make_slack_payload(organization=organization)

    step = FinishDirectPaging(slack_team_identity)
    with patch.object(step._slack_client, "api_call"):
        response = step.process_scenario(slack_user_identity, slack_team_identity, payload)
    response = response.data

    assert response["response_action"] == "update"
    assert (
        response["view"]["blocks"][0]["text"]["text"] == ":no_entry: You do not have permission to perform this action."
    )


@pytest.mark.django_db
def test_trigger_paging_additional_responders(make_organization_and_user_with_slack_identities, make_team):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)
    payload = make_slack_payload(organization=organization, team=team, current_users={str(user.pk): Policy.IMPORTANT})

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    mock_direct_paging.assert_called_once_with(
        organization=organization,
        from_user=user,
        message="The Message",
        team=team,
        users=[(user, True)],
    )


@pytest.mark.django_db
def test_page_team(make_organization_and_user_with_slack_identities, make_team):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)
    payload = make_slack_payload(organization=organization, team=team)

    step = FinishDirectPaging(slack_team_identity)
    with patch("apps.slack.scenarios.paging.direct_paging") as mock_direct_paging:
        with patch.object(step._slack_client, "api_call"):
            step.process_scenario(slack_user_identity, slack_team_identity, payload)

    mock_direct_paging.assert_called_once_with(
        organization=organization,
        from_user=user,
        message="The Message",
        team=team,
        users=[],
    )


@pytest.mark.django_db
def test_get_organization_select(make_organization):
    organization = make_organization(org_title="Organization", stack_slug="stack_slug")
    select = _get_organization_select(Organization.objects.filter(pk=organization.pk), organization, "test")

    assert len(select["element"]["options"]) == 1
    assert json.loads(select["element"]["options"][0]["value"]) == json.loads(
        make_value({"id": organization.pk}, organization)
    )
    assert select["element"]["options"][0]["text"]["text"] == "Organization (stack_slug)"


@pytest.mark.django_db
def test_get_team_select_blocks(
    make_organization_and_user_with_slack_identities,
    make_team,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
):
    info_msg = (
        "*Note*: You can only page teams which have a Direct Paging integration that is configured. "
        "<https://grafana.com/docs/oncall/latest/integrations/manual/#set-up-direct-paging-for-a-team|Learn more>"
    )

    input_id_prefix = "nmxcnvmnxv"

    def _contstruct_team_option(team):
        return {
            "text": {"emoji": True, "text": team.name, "type": "plain_text"},
            "value": make_value({"id": team.pk}, organization),
        }

    # no team selected - no team direct paging integrations available
    organization, _, _, slack_user_identity = make_organization_and_user_with_slack_identities()
    blocks = _get_team_select_blocks(slack_user_identity, organization, False, None, input_id_prefix)

    assert len(blocks) == 1

    context_block = blocks[0]
    assert context_block["type"] == "context"
    assert (
        context_block["elements"][0]["text"]
        == info_msg + ". There are currently no teams which have a Direct Paging integration that is configured."
    )

    # no team selected - 1 team direct paging integration available
    organization, _, _, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)
    arc = make_alert_receive_channel(organization, team=team, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)
    escalation_chain = make_escalation_chain(organization)
    make_channel_filter(arc, is_default=True, escalation_chain=escalation_chain)

    blocks = _get_team_select_blocks(slack_user_identity, organization, False, None, input_id_prefix)

    assert len(blocks) == 2
    input_block, context_block = blocks

    assert input_block["type"] == "input"
    assert len(input_block["element"]["options"]) == 1
    assert input_block["element"]["options"] == [_contstruct_team_option(team)]
    assert context_block["elements"][0]["text"] == info_msg

    # team selected
    organization, _, _, slack_user_identity = make_organization_and_user_with_slack_identities()
    team1 = make_team(organization)
    team2 = make_team(organization)

    def _setup_direct_paging_integration(team):
        arc = make_alert_receive_channel(
            organization, team=team, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
        )
        escalation_chain = make_escalation_chain(organization)
        make_channel_filter(arc, is_default=True, escalation_chain=escalation_chain)
        return arc

    _setup_direct_paging_integration(team1)
    team2_direct_paging_arc = _setup_direct_paging_integration(team2)

    blocks = _get_team_select_blocks(slack_user_identity, organization, True, team2, input_id_prefix)

    assert len(blocks) == 2
    input_block, context_block = blocks

    team1_option = _contstruct_team_option(team1)
    team2_option = _contstruct_team_option(team2)

    def _sort_team_options(options):
        return sorted(options, key=lambda o: o["value"])

    assert input_block["type"] == "input"
    assert len(input_block["element"]["options"]) == 2
    assert _sort_team_options(input_block["element"]["options"]) == _sort_team_options([team1_option, team2_option])
    assert input_block["element"]["initial_option"] == team2_option

    assert (
        context_block["elements"][0]["text"]
        == f"Integration <{team2_direct_paging_arc.web_link}|{team2_direct_paging_arc.verbal_name}> will be used for notification."
    )

    # team's direct paging integration has two routes associated with it
    # the team should only be displayed once
    organization, _, _, slack_user_identity = make_organization_and_user_with_slack_identities()
    team = make_team(organization)

    arc = make_alert_receive_channel(organization, team=team, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)
    escalation_chain = make_escalation_chain(organization)
    make_channel_filter(arc, is_default=True, escalation_chain=escalation_chain)
    make_channel_filter(arc, escalation_chain=escalation_chain)

    blocks = _get_team_select_blocks(slack_user_identity, organization, False, None, input_id_prefix)

    assert len(blocks) == 2
    input_block, context_block = blocks

    assert input_block["type"] == "input"
    assert len(input_block["element"]["options"]) == 1
    assert json.loads(input_block["element"]["options"][0]["value"]) == json.loads(
        _contstruct_team_option(team)["value"]
    )
    assert context_block["elements"][0]["text"] == info_msg
