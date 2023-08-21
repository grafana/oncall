from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from apps.heartbeat.tasks import check_heartbeats
from apps.integrations.tasks import create_alert


@pytest.mark.django_db
@pytest.mark.parametrize("integration", [AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK])
def test_check_heartbeats(
    make_organization_and_user,
    make_alert_receive_channel,
    make_integration_heartbeat,
    integration,
    django_capture_on_commit_callbacks,
):
    # No heartbeats, nothing happens
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 0 expired and 0 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 0

    # Prepare heartbeat
    team, _ = make_organization_and_user()
    timeout = 60
    last_heartbeat_time = timezone.now()
    alert_receive_channel = make_alert_receive_channel(team, integration=integration)
    integration_heartbeat = make_integration_heartbeat(
        alert_receive_channel, timeout, last_heartbeat_time=last_heartbeat_time, previous_alerted_state_was_life=True
    )

    # Heartbeat is alive, nothing happens
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 0 expired and 0 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 0

    # Hearbeat expires, send an alert
    integration_heartbeat.refresh_from_db()
    integration_heartbeat.last_heartbeat_time = timezone.now() - timezone.timedelta(seconds=timeout * 10)
    integration_heartbeat.save()
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 1 expired and 0 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 1

    # Heartbeat is still expired, nothing happens
    integration_heartbeat.refresh_from_db()
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 0 expired and 0 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 0

    # Hearbeat restored, send an auto-resolve alert
    integration_heartbeat.refresh_from_db()
    integration_heartbeat.last_heartbeat_time = timezone.now()
    integration_heartbeat.save()
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 0 expired and 1 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 1

    # Heartbeat is alive, nothing happens
    integration_heartbeat.refresh_from_db()
    integration_heartbeat.last_heartbeat_time = timezone.now()
    integration_heartbeat.save()
    integration_heartbeat.refresh_from_db()
    with patch.object(create_alert, "apply_async") as mock_create_alert_apply_async:
        with django_capture_on_commit_callbacks(execute=True):
            result = check_heartbeats()
    assert result == "Found 0 expired and 0 restored heartbeats"
    assert mock_create_alert_apply_async.call_count == 0
