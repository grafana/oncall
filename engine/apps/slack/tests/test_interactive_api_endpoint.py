import json
from unittest.mock import call, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.slack.scenarios.scenario_step import PAYLOAD_TYPE_BLOCK_ACTIONS

EVENT_TRIGGER_ID = "5333959822612.4122782784722.4734ff484b2ac4d36a185bb242ee9932"
WARNING_TEXT = (
    "OnCall is not able to process this action because one of the following scenarios: \n"
    "1. The Slack chatops integration was disconnected from the instance that the Alert Group belongs "
    "to, BUT the Slack workspace is still connected to another instance as well. In this case, simply log "
    "in to the OnCall web interface and re-install the Slack Integration with this workspace again.\n"
    "2. (Less likely) The Grafana instance belonging to this Alert Group was deleted. In this case the Alert Group is orphaned and cannot be acted upon."
)


def _make_request(payload):
    return APIClient().post(
        "/slack/interactive_api_endpoint/",
        format="json",
        data=payload,
        **{
            "HTTP_X_SLACK_SIGNATURE": "asdfasdf",
            "HTTP_X_SLACK_REQUEST_TIMESTAMP": "xxcxcvx",
        },
    )


@patch("apps.slack.views.SlackEventApiEndpointView.verify_signature", return_value=True)
@patch("apps.slack.views.SlackEventApiEndpointView._open_warning_window_if_needed")
@pytest.mark.django_db
def test_organization_not_found_scenario_properly_handled(
    mock_open_warning_window_if_needed,
    _mock_verify_signature,
    make_organization,
    make_slack_user_identity,
    make_slack_team_identity,
):
    slack_team_id = "T043LP0P2M8"
    slack_access_token = "asdfasdf"
    slack_bot_access_token = "cmncvmnvcnm"
    slack_bot_user_id = "mncvnmvcmnvcmncv,,cx,"

    slack_user_id = "iurtiurituritu"

    def _make_slack_team_identity():
        return make_slack_team_identity(
            slack_id=slack_team_id,
            detected_token_revoked=None,
            access_token=slack_access_token,
            bot_access_token=slack_bot_access_token,
            bot_user_id=slack_bot_user_id,
        )

    # SCENARIO 1
    # two orgs connected to same slack workspace, the one belonging to the alert group/slack message
    # is no longer connected to the slack workspace, but another org still is
    slack_team_identity = _make_slack_team_identity()
    make_slack_user_identity(slack_team_identity=slack_team_identity, slack_id=slack_user_id)

    make_organization(slack_team_identity=slack_team_identity)
    org2 = make_organization()
    event_payload_actions = [
        {
            "value": json.dumps({"organization_id": org2.id}),
        }
    ]

    event_payload = {
        "type": PAYLOAD_TYPE_BLOCK_ACTIONS,
        "trigger_id": EVENT_TRIGGER_ID,
        "user": {
            "id": slack_user_id,
        },
        "team": {
            "id": slack_team_id,
        },
        "actions": event_payload_actions,
    }

    response = _make_request(event_payload)
    assert response.status_code == status.HTTP_200_OK

    # SCENARIO 2
    # the org that was associated w/ the alert group, has since been deleted
    # and the slack message is now orphaned
    org2.hard_delete()

    response = _make_request(event_payload)
    assert response.status_code == status.HTTP_200_OK

    mock_call = call(event_payload, slack_team_identity, WARNING_TEXT)
    mock_open_warning_window_if_needed.assert_has_calls([mock_call, mock_call])
