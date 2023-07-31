import pytest

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import disable_maintenance
from common.exceptions import MaintenanceCouldNotBeStartedError


@pytest.fixture()
def maintenance_test_setup(
    make_organization_and_user,
    make_escalation_chain,
):
    organization, user = make_organization_and_user()
    make_escalation_chain(organization)
    return organization, user


@pytest.mark.django_db
def test_start_maintenance_integration(
    maintenance_test_setup, make_alert_receive_channel, mock_start_disable_maintenance_task
):
    organization, user = maintenance_test_setup

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, author=user
    )
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds

    alert_receive_channel.start_maintenance(mode, duration, user)

    assert alert_receive_channel.maintenance_mode == mode
    assert alert_receive_channel.maintenance_duration == AlertReceiveChannel.DURATION_ONE_HOUR
    assert alert_receive_channel.maintenance_uuid is not None
    assert alert_receive_channel.maintenance_started_at is not None
    assert alert_receive_channel.maintenance_author == user


@pytest.mark.django_db
def test_start_maintenance_integration_multiple_previous_instances(
    maintenance_test_setup, make_alert_receive_channel, mock_start_disable_maintenance_task
):
    organization, user = maintenance_test_setup

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, author=user
    )
    # 2 maintenance integrations were created in the past
    for i in range(2):
        AlertReceiveChannel.create(
            organization=organization, integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE, author=user
        )

    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds

    alert_receive_channel.start_maintenance(mode, duration, user)

    assert alert_receive_channel.maintenance_mode == mode
    assert alert_receive_channel.maintenance_duration == AlertReceiveChannel.DURATION_ONE_HOUR
    assert alert_receive_channel.maintenance_uuid is not None
    assert alert_receive_channel.maintenance_started_at is not None
    assert alert_receive_channel.maintenance_author == user


@pytest.mark.django_db
def test_maintenance_integration_will_not_start_twice(
    maintenance_test_setup, make_alert_receive_channel, mock_start_disable_maintenance_task
):
    organization, user = maintenance_test_setup

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, author=user
    )
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds

    alert_receive_channel.start_maintenance(mode, duration, user)
    with pytest.raises(MaintenanceCouldNotBeStartedError):
        alert_receive_channel.start_maintenance(mode, duration, user)

    assert alert_receive_channel.maintenance_mode == mode
    assert alert_receive_channel.maintenance_duration == AlertReceiveChannel.DURATION_ONE_HOUR
    assert alert_receive_channel.maintenance_uuid is not None
    assert alert_receive_channel.maintenance_started_at is not None
    assert alert_receive_channel.maintenance_author == user


@pytest.mark.django_db
def test_alert_attached_to_maintenance_incident_integration(
    maintenance_test_setup,
    make_alert_receive_channel,
    make_alert_with_custom_create_method,
    mock_start_disable_maintenance_task,
):
    organization, user = maintenance_test_setup

    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds

    alert_receive_channel.start_maintenance(mode, duration, user)
    maintenance_incident = AlertGroup.objects.get(maintenance_uuid=alert_receive_channel.maintenance_uuid)

    alert = make_alert_with_custom_create_method(
        title="test_title",
        message="test_message",
        image_url="test_img_url",
        link_to_upstream_details=None,
        alert_receive_channel=alert_receive_channel,
        raw_request_data={"message": "test"},
        integration_unique_data={},
    )

    assert alert.group.root_alert_group == maintenance_incident


@pytest.mark.django_db(transaction=True)
def test_stop_maintenance(
    maintenance_test_setup,
    make_alert_receive_channel,
    make_alert_with_custom_create_method,
    mock_start_disable_maintenance_task,
):
    organization, user = maintenance_test_setup
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds

    alert_receive_channel.start_maintenance(mode, duration, user)
    maintenance_incident = AlertGroup.objects.get(maintenance_uuid=alert_receive_channel.maintenance_uuid)
    alert = make_alert_with_custom_create_method(
        title="test_title",
        message="test_message",
        image_url="test_img_url",
        link_to_upstream_details=None,
        alert_receive_channel=alert_receive_channel,
        raw_request_data={"message": "test"},
        integration_unique_data={},
    )

    disable_maintenance(alert_receive_channel_id=alert_receive_channel.pk, force=True)
    maintenance_incident.refresh_from_db()
    alert.refresh_from_db()
    assert maintenance_incident.resolved_by == AlertGroup.DISABLE_MAINTENANCE
    assert alert.group.resolved_by == AlertGroup.DISABLE_MAINTENANCE
