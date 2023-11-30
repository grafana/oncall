from unittest.mock import patch, call

import pytest
from apps.alerts.tasks.notify_team import notify_team_task
from apps.api.permissions import LegacyAccessControlRole



@pytest.mark.django_db
def test_notify_team(
    make_organization,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_team
):
    organization = make_organization()
    user_1 = make_user(
        organization=organization, role=LegacyAccessControlRole.VIEWER, _verified_phone_number="1234567890"
    )
    user_2 = make_user(
        organization=organization, role=LegacyAccessControlRole.VIEWER, _verified_phone_number="1234567890"
    )
    user_3 = make_user(
        organization=organization, role=LegacyAccessControlRole.VIEWER, _verified_phone_number="1234567890"
    )
    team_1 = make_team(
        organization=organization,
    )
    team_1.users.add(user_1)
    team_1.users.add(user_2)
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    with patch("apps.alerts.tasks.notify_team.notify_user_task") as mock_execute:
        notify_team_task(team_1.pk, alert_group.pk)
    
    assert mock_execute.call_args_list[0] == call(user_1.pk, alert_group.pk, None, None, False, False, False, False)
    assert mock_execute.call_args_list[1] == call(user_2.pk, alert_group.pk, None, None, False, False, False, False)
    assert mock_execute.call_count == 2

