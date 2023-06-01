import pytest
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel


@pytest.mark.django_db
def test_silence_alert_group(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    mock_start_disable_maintenance_task,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.silence()

    assert alert_group.silenced is True
    assert alert_group.silenced_at is not None


@pytest.mark.django_db
def test_silence_by_user_alert_group(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    mock_start_disable_maintenance_task,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    alert_group = make_alert_group(alert_receive_channel)
    alert_group.silence()

    assert alert_group.silenced is True
    assert alert_group.silenced_at is not None


@pytest.mark.django_db
def test_unsilence_alert_group(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    mock_start_disable_maintenance_task,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    now = timezone.now()
    silenced_until = now + timezone.timedelta(seconds=3600)
    alert_group = make_alert_group(
        alert_receive_channel,
        silenced=True,
        silenced_at=timezone.now(),
        silenced_by_user=user,
        silenced_until=silenced_until,
    )
    alert_group.un_silence()

    assert alert_group.silenced is False
    assert alert_group.silenced_at is None
    assert alert_group.silenced_until is None
    assert alert_group.silenced_by_user is None
    assert alert_group.restarted_at is not None
