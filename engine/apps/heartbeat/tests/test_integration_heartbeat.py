from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel


@pytest.mark.django_db
@patch("apps.heartbeat.models.IntegrationHeartBeat.on_heartbeat_expired", return_value=None)
@pytest.mark.parametrize("integration", [AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK])
def test_integration_heartbeat_expired(
    mocked_handler, make_organization_and_user, make_alert_receive_channel, make_integration_heartbeat, integration
):
    amixr_team, _ = make_organization_and_user()
    # Some short timeout and last_heartbeat_time to make sure that heartbeat is expired
    timeout = 1
    last_heartbeat_time = timezone.now() - timezone.timedelta(seconds=timeout * 10)
    alert_receive_channel = make_alert_receive_channel(amixr_team, integration=integration)
    integration_heartbeat = make_integration_heartbeat(
        alert_receive_channel, timeout, last_heartbeat_time=last_heartbeat_time
    )
    integration_heartbeat.check_heartbeat_state_and_save()
    assert mocked_handler.called


@pytest.mark.django_db
@patch("apps.heartbeat.models.IntegrationHeartBeat.on_heartbeat_expired", return_value=None)
@pytest.mark.parametrize("integration", [AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK])
def test_integration_heartbeat_already_expired(
    mocked_handler, make_organization_and_user, make_alert_receive_channel, make_integration_heartbeat, integration
):
    amixr_team, _ = make_organization_and_user()
    # Some short timeout and last_heartbeat_time to make sure that heartbeat is expired
    timeout = 1
    last_heartbeat_time = timezone.now() - timezone.timedelta(seconds=timeout * 10)
    alert_receive_channel = make_alert_receive_channel(amixr_team, integration=integration)
    integration_heartbeat = make_integration_heartbeat(
        alert_receive_channel,
        timeout,
        last_heartbeat_time=last_heartbeat_time,
        previous_alerted_state_was_life=False,
    )
    integration_heartbeat.check_heartbeat_state_and_save()
    assert mocked_handler.called is False


@pytest.mark.django_db
@patch("apps.heartbeat.models.IntegrationHeartBeat.on_heartbeat_restored", return_value=None)
@pytest.mark.parametrize("integration", [AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK])
def test_integration_heartbeat_restored(
    mocked_handler, make_organization_and_user, make_alert_receive_channel, make_integration_heartbeat, integration
):
    amixr_team, _ = make_organization_and_user()
    # Some long timeout and last_heartbeat_time to make sure that heartbeat is not expired
    timeout = 1000
    last_heartbeat_time = timezone.now()
    alert_receive_channel = make_alert_receive_channel(amixr_team, integration=integration)
    integration_heartbeat = make_integration_heartbeat(
        alert_receive_channel,
        timeout,
        last_heartbeat_time=last_heartbeat_time,
        previous_alerted_state_was_life=False,
    )
    integration_heartbeat.check_heartbeat_state_and_save()
    assert mocked_handler.called


@pytest.mark.django_db
@patch("apps.heartbeat.models.IntegrationHeartBeat.on_heartbeat_restored", return_value=None)
@pytest.mark.parametrize("integration", [AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK])
def test_integration_heartbeat_restored_and_alert_was_not_sent(
    mocked_handler, make_organization_and_user, make_alert_receive_channel, make_integration_heartbeat, integration
):
    amixr_team, _ = make_organization_and_user()
    # Some long timeout and last_heartbeat_time to make sure that heartbeat is not expired
    timeout = 1000
    last_heartbeat_time = timezone.now()
    alert_receive_channel = make_alert_receive_channel(amixr_team, integration=integration)
    integration_heartbeat = make_integration_heartbeat(
        alert_receive_channel,
        timeout,
        last_heartbeat_time=last_heartbeat_time,
    )
    integration_heartbeat.check_heartbeat_state_and_save()
    assert mocked_handler.called is False
