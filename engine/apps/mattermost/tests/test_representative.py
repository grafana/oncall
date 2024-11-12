import pytest
from django.utils import timezone

from apps.alerts.models import AlertGroupLogRecord, AlertReceiveChannel
from apps.mattermost.alert_group_representative import AlertGroupMattermostRepresentative


@pytest.mark.django_db
def test_get_handler(
    make_organization,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_at=timezone.now() + timezone.timedelta(hours=1),
        acknowledged=True,
    )
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)
    handler = AlertGroupMattermostRepresentative(log_record=log_record).get_handler()
    assert handler.__name__ == "on_alert_group_action"


@pytest.mark.django_db
def test_is_applicable_success(
    make_organization,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_at=timezone.now() + timezone.timedelta(hours=1),
        acknowledged=True,
    )
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)
    assert AlertGroupMattermostRepresentative(log_record=log_record).is_applicable()


@pytest.mark.django_db
def test_is_applicable_without_channels(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    ack_alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_at=timezone.now() + timezone.timedelta(hours=1),
        acknowledged=True,
    )
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_ACK, author=None)
    assert not AlertGroupMattermostRepresentative(log_record=log_record).is_applicable()


@pytest.mark.django_db
def test_is_applicable_invalid_type(
    make_organization,
    make_alert_receive_channel,
    make_mattermost_channel,
    make_alert_group,
    make_alert,
    make_alert_group_log_record,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    make_mattermost_channel(organization=organization, is_default_channel=True)
    ack_alert_group = make_alert_group(
        alert_receive_channel=alert_receive_channel,
        acknowledged_at=timezone.now() + timezone.timedelta(hours=1),
        acknowledged=True,
    )
    make_alert(alert_group=ack_alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    log_record = make_alert_group_log_record(ack_alert_group, type=AlertGroupLogRecord.TYPE_RE_INVITE, author=None)
    assert not AlertGroupMattermostRepresentative(log_record=log_record).is_applicable()
