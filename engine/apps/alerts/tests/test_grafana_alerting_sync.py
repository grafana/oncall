import pytest

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager


@pytest.mark.django_db
def test_find_name_of_contact_point_grafana_datasource(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    sync_manager = GrafanaAlertingSyncManager(alert_receive_channel)

    receivers = [
        {"name": "autogen-contact-point-default"},
        {
            "name": "testing",
            "grafana_managed_receiver_configs": [
                {
                    "uid": "some-uid",
                    "name": "testing",
                }
            ],
        },
    ]

    name = sync_manager.find_name_of_contact_point("some-uid", True, receivers)
    assert name == "testing"
