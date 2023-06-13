from unittest.mock import MagicMock

import pytest

from apps.telegram.renderers.keyboard import Action
from apps.telegram.updates.update_handlers.button_press import ButtonPressHandler


@pytest.mark.django_db
def test_get_action_context(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
):
    """
    Test to ensure that both legacy action_name and action_code format is supported.
    """
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(
        organization,
    )
    alert_group = make_alert_group(alert_receive_channel)

    handler = ButtonPressHandler(MagicMock())

    ack_data_with_action_name = f"{alert_group.id}:acknowledge:oncall-uuid{organization.uuid}"
    ack_data_with_action_code = f"{alert_group.id}:0:oncall-uuid{organization.uuid}"

    unack_data_with_action_name = f"{alert_group.id}:unacknowledge:oncall-uuid{organization.uuid}"
    unack_data_with_action_code = f"{alert_group.id}:1:oncall-uuid{organization.uuid}"

    resolve_data_with_action_name = f"{alert_group.id}:resolve:oncall-uuid{organization.uuid}"
    resolve_data_with_action_code = f"{alert_group.id}:2:oncall-uuid{organization.uuid}"

    unresolve_data_with_action_name = f"{alert_group.id}:unresolve:oncall-uuid{organization.uuid}"
    unresolve_data_with_action_code = f"{alert_group.id}:3:oncall-uuid{organization.uuid}"

    silence_data_with_action_name = f"{alert_group.id}:silence:3600:oncall-uuid{organization.uuid}"
    silence_data_with_action_code = f"{alert_group.id}:4:3600:oncall-uuid{organization.uuid}"

    unsilence_data_with_action_name = f"{alert_group.id}:unsilence:oncall-uuid{organization.uuid}"
    unsilence_data_with_action_code = f"{alert_group.id}:5:oncall-uuid{organization.uuid}"

    ACTION_TO_DATA_STR = {
        Action.ACKNOWLEDGE: [ack_data_with_action_name, ack_data_with_action_code],
        Action.UNACKNOWLEDGE: [unack_data_with_action_name, unack_data_with_action_code],
        Action.RESOLVE: [resolve_data_with_action_name, resolve_data_with_action_code],
        Action.UNRESOLVE: [unresolve_data_with_action_name, unresolve_data_with_action_code],
        Action.SILENCE: [silence_data_with_action_name, silence_data_with_action_code],
        Action.UNSILENCE: [unsilence_data_with_action_name, unsilence_data_with_action_code],
    }
    action_context = handler._get_action_context(ack_data_with_action_name)

    for action, data_strings in ACTION_TO_DATA_STR.items():
        for data_str in data_strings:
            action_context = handler._get_action_context(data_str)
            assert action_context.action.value == action.value
