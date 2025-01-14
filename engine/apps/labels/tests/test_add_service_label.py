import pytest

from apps.alerts.constants import SERVICE_LABEL, SERVICE_LABEL_TEMPLATE_FOR_ALERTING_INTEGRATION
from apps.alerts.models import AlertReceiveChannel
from apps.labels.tasks import add_service_label_per_org


@pytest.mark.django_db
def test_add_service_label_per_org(make_organization, make_alert_receive_channel, make_label_key):
    organization = make_organization()
    alert_receive_channel_alerting_no_labels = make_alert_receive_channel(
        organization=organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )
    alert_receive_channel_alerting_with_label = make_alert_receive_channel(
        organization=organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        alert_group_labels_custom=[["test", None, "test_template"]],
    )
    alert_receive_channel_grafana = make_alert_receive_channel(
        organization=organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    service_name_label_key = make_label_key(organization, key_id="service_label_id", key_name=SERVICE_LABEL)

    expected_service_name_label = [service_name_label_key.id, None, SERVICE_LABEL_TEMPLATE_FOR_ALERTING_INTEGRATION]

    add_service_label_per_org(organization.id)

    for alert_receive_channel in [
        alert_receive_channel_alerting_no_labels,
        alert_receive_channel_alerting_with_label,
        alert_receive_channel_grafana,
    ]:
        alert_receive_channel.refresh_from_db()

    assert alert_receive_channel_alerting_no_labels.alert_group_labels_custom == [expected_service_name_label]
    assert alert_receive_channel_alerting_with_label.alert_group_labels_custom == [
        expected_service_name_label,
        ["test", None, "test_template"],
    ]
    assert alert_receive_channel_grafana.alert_group_labels_custom is None
