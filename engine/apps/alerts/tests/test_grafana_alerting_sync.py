import copy
from unittest.mock import PropertyMock, patch

import pytest

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.models import AlertReceiveChannel
from apps.grafana_plugin.helpers import GrafanaAPIClient

TEST_INTEGRATION_URL = "/some/test/url"
ALERTMANAGER_ACTIVE_RECEIVER_1 = "test-receiver"
ALERTMANAGER_ACTIVE_RECEIVER_2 = "test-receiver-empty"
ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED = "test-receiver-oncall-connected"
ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED = "test-receiver-inactive-oncall-connected"
RECEIVER_NAME_NOT_IN_CONFIG = "test-receiver-not-in-config"

GRAFANA_ALERTMANAGER_CONFIG = {
    "template_files": {},
    "alertmanager_config": {
        "route": {
            "receiver": ALERTMANAGER_ACTIVE_RECEIVER_1,
            "group_by": ["grafana_folder", "alertname"],
            "routes": [
                {
                    "receiver": ALERTMANAGER_ACTIVE_RECEIVER_1,
                    "continue": True,
                    "routes": [
                        {
                            "receiver": ALERTMANAGER_ACTIVE_RECEIVER_2,
                            "continue": True,
                        }
                    ],
                },
                {
                    "receiver": ALERTMANAGER_ACTIVE_RECEIVER_2,
                    "continue": True,
                    "routes": [
                        {
                            "receiver": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                            "continue": True,
                        }
                    ],
                },
            ],
        },
        "templates": None,
        "receivers": [
            {
                "name": ALERTMANAGER_ACTIVE_RECEIVER_1,
                "grafana_managed_receiver_configs": [
                    {
                        "uid": "test_uid_1",
                        "name": "email receiver",
                        "type": "email",
                        "disableResolveMessage": False,
                        "settings": {"addresses": "<example@email.com>"},
                        "secureFields": {},
                    }
                ],
            },
            {"name": ALERTMANAGER_ACTIVE_RECEIVER_2},
            {
                "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                "grafana_managed_receiver_configs": [
                    {
                        "uid": "test_uid_2",
                        "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                        "type": "webhook",
                        "disableResolveMessage": False,
                        "settings": {
                            "httpMethod": "POST",
                            "url": TEST_INTEGRATION_URL,
                        },
                        "secureFields": {},
                    },
                    {
                        "uid": "test_uid_3",
                        "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                        "type": "oncall",
                        "disableResolveMessage": False,
                        "settings": {
                            "httpMethod": "POST",
                            "url": TEST_INTEGRATION_URL,
                        },
                        "secureFields": {},
                    },
                ],
            },
            {
                "name": ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED,
                "grafana_managed_receiver_configs": [
                    {
                        "uid": "test_uid_4",
                        "name": ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED,
                        "type": "webhook",
                        "disableResolveMessage": False,
                        "settings": {
                            "httpMethod": "POST",
                            "url": TEST_INTEGRATION_URL,
                        },
                        "secureFields": {},
                    },
                    {
                        "uid": "test_uid_5",
                        "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                        "type": "email",
                        "disableResolveMessage": False,
                        "settings": {"addresses": "<example@email.com>"},
                        "secureFields": {},
                    },
                ],
            },
        ],
    },
}

MIMIR_ALERTMANAGER_CONFIG = {
    "template_files": {},
    "alertmanager_config": {
        "receivers": [
            {
                "name": ALERTMANAGER_ACTIVE_RECEIVER_1,
                "webhook_configs": [
                    {
                        "send_resolved": True,
                        "url": "some/webhook/url",
                    }
                ],
            },
            {"name": ALERTMANAGER_ACTIVE_RECEIVER_2},
            {
                "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                "webhook_configs": [
                    {
                        "send_resolved": True,
                        "url": TEST_INTEGRATION_URL,
                    }
                ],
            },
            {
                "name": ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED,
                "webhook_configs": [
                    {
                        "send_resolved": True,
                        "url": TEST_INTEGRATION_URL,
                    },
                    {"send_resolved": True, "url": "https://example.com"},
                ],
            },
        ],
        "route": {
            "group_wait": "0s",
            "receiver": ALERTMANAGER_ACTIVE_RECEIVER_1,
            "routes": [
                {
                    "continue": True,
                    "group_by": [],
                    "matchers": [],
                    "receiver": ALERTMANAGER_ACTIVE_RECEIVER_1,
                    "routes": [
                        {
                            "continue": True,
                            "group_by": [],
                            "matchers": [],
                            "receiver": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                            "routes": [
                                {
                                    "continue": True,
                                    "group_by": [],
                                    "matchers": [],
                                    "receiver": ALERTMANAGER_ACTIVE_RECEIVER_2,
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "templates": [],
    },
}

# response on /datasources endpoint
DATASOURCES = [
    {
        "id": 1,
        "uid": "some_uid",
        "orgId": 1,
        "name": "Mimir",
        "type": "prometheus",
        "typeName": "Prometheus",
        "typeLogoUrl": "public/app/plugins/datasource/prometheus/img/prometheus_logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {
            "alertmanagerUid": "alertmanager",
        },
        "readOnly": False,
    },
    {
        "id": 2,
        "uid": "some_uid_2",
        "orgId": 1,
        "name": "Mimir Alertmanager",
        "type": "alertmanager",
        "typeName": "Alertmanager",
        "typeLogoUrl": "public/app/plugins/datasource/alertmanager/img/logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {"implementation": "cortex"},
        "readOnly": False,
    },
    {
        "id": 3,
        "uid": "grafanacloud-ngalertmanager",
        "orgId": 1,
        "name": "grafanacloud-test-ngalertmanager",
        "type": "alertmanager",
        "typeName": "Alertmanager",
        "typeLogoUrl": "public/app/plugins/datasource/alertmanager/img/logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": False,
        "readOnly": False,
    },
    {
        "id": 4,
        "uid": "some_uid_3",
        "orgId": 1,
        "name": "Mimir Alertmanager 2",
        "type": "alertmanager",
        "typeName": "Alertmanager",
        "typeLogoUrl": "public/app/plugins/datasource/alertmanager/img/logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {"implementation": "mimir"},
        "readOnly": False,
    },
    {
        "id": 5,
        "uid": "some_uid_4",
        "orgId": 1,
        "name": "Prometheus Alertmanager",
        "type": "alertmanager",
        "typeName": "Alertmanager",
        "typeLogoUrl": "public/app/plugins/datasource/alertmanager/img/logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {"implementation": "prometheus"},
        "readOnly": False,
    },
    {
        "id": 6,
        "uid": "some_uid_5",
        "orgId": 1,
        "name": "Another Alertmanager",
        "type": "alertmanager",
        "typeName": "Alertmanager",
        "typeLogoUrl": "public/app/plugins/datasource/alertmanager/img/logo.svg",
        "access": "proxy",
        "url": "test/url/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "isDefault": False,
        "jsonData": {},
        "readOnly": False,
    },
]


@pytest.mark.django_db
def test_get_datasources():
    client = GrafanaAPIClient("/test/url", "test_token")
    grafana_alerting_datasource = {
        "uid": GrafanaAlertingSyncManager.GRAFANA_ALERTING_DATASOURCE,
        "name": "Grafana",
    }
    valid_datasource_ids = [2, 3, 4]
    valid_datasources = [grafana_alerting_datasource] + [ds for ds in DATASOURCES if ds["id"] in valid_datasource_ids]
    expected_result = [{"uid": ds["uid"], "name": ds["name"]} for ds in valid_datasources]
    with patch("apps.grafana_plugin.helpers.GrafanaAPIClient.get_datasources", return_value=(DATASOURCES, {})):
        result = GrafanaAlertingSyncManager.get_datasources(client)

    assert result == expected_result


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana"),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid"),
        (None, "some_uid"),
    ],
)
@pytest.mark.django_db
def test_get_connected_contact_points_from_config(
    mocked_integration_url, alertmanager_config, datasource_uid, make_organization, make_alert_receive_channel
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager
    expected_contact_points = (
        [
            {
                "name": ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
                "notification_connected": True,
            },
            {
                "name": ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED,
                "notification_connected": False,
            },
        ]
        if alertmanager_config
        else []
    )

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(alertmanager_config, {}),
    ):
        connected_contact_points = sync_manager.get_connected_contact_points_for_datasource(datasource_uid)
        assert connected_contact_points == expected_contact_points


@pytest.mark.django_db
def test_get_contact_points_from_config(make_alert_receive_channel):
    client = GrafanaAPIClient("/test/url", "test_token")
    expected_contact_points = [
        ALERTMANAGER_ACTIVE_RECEIVER_1,
        ALERTMANAGER_ACTIVE_RECEIVER_2,
        ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED,
        ALERTMANAGER_INACTIVE_RECEIVER_CONNECTED,
    ]

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(GRAFANA_ALERTMANAGER_CONFIG, {}),
    ):
        contact_points = GrafanaAlertingSyncManager.get_contact_points_for_datasource(client, "grafana")
        assert contact_points == expected_contact_points

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(MIMIR_ALERTMANAGER_CONFIG, {}),
    ):
        contact_points = GrafanaAlertingSyncManager.get_contact_points_for_datasource(client, "some_uid")
        assert contact_points == expected_contact_points

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(None, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.get_default_mimir_alertmanager_config_for_datasource",
            return_value=None,
        ) as mocked_get_default_config:
            result = GrafanaAlertingSyncManager.get_contact_points_for_datasource(client, "some_uid")
            assert result is None
            assert mocked_get_default_config.called

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(None, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.get_default_mimir_alertmanager_config_for_datasource",
            return_value=None,
        ) as mocked_get_default_config:
            result = GrafanaAlertingSyncManager.get_contact_points_for_datasource(client, "grafana")
            assert result is None
            assert not mocked_get_default_config.called


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.check_if_oncall_type_is_available",
    return_value=True,
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid,contact_point_name,create_new",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", ALERTMANAGER_ACTIVE_RECEIVER_1, False),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", ALERTMANAGER_ACTIVE_RECEIVER_1, False),
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", ALERTMANAGER_ACTIVE_RECEIVER_1, True),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", ALERTMANAGER_ACTIVE_RECEIVER_1, True),
    ],
)
@pytest.mark.django_db
def test_connect_contact_point_existing(
    mocked_integration_url,
    mocked_contact_point_type_check,
    alertmanager_config,
    datasource_uid,
    contact_point_name,
    create_new,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(alertmanager_config, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.update_alerting_config_for_datasource",
            return_value="OK",
        ) as update_config:
            result, error = sync_manager.connect_contact_point(datasource_uid, contact_point_name, create_new)
            if create_new:
                assert (result, error) == (False, "Contact point already exists")
                assert not update_config.called
            else:
                updated_config = update_config.call_args.args[-1]
                assert (result, error) == (True, "")

                contact_point = updated_config["alertmanager_config"]["receivers"][0]
                assert contact_point["name"] == ALERTMANAGER_ACTIVE_RECEIVER_1
                if datasource_uid == "grafana":
                    assert (
                        contact_point["grafana_managed_receiver_configs"][-1]["settings"]["url"] == TEST_INTEGRATION_URL
                    )
                    assert contact_point["grafana_managed_receiver_configs"][-1]["type"] == "oncall"
                else:
                    assert contact_point["oncall_configs"][-1]["url"] == TEST_INTEGRATION_URL


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.check_if_oncall_type_is_available",
    return_value=True,
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid,contact_point_name,create_new",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", RECEIVER_NAME_NOT_IN_CONFIG, False),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", RECEIVER_NAME_NOT_IN_CONFIG, False),
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", RECEIVER_NAME_NOT_IN_CONFIG, True),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", RECEIVER_NAME_NOT_IN_CONFIG, True),
    ],
)
@pytest.mark.django_db
def test_connect_contact_point_not_existing(
    mocked_integration_url,
    mocked_contact_point_type_check,
    alertmanager_config,
    datasource_uid,
    contact_point_name,
    create_new,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(alertmanager_config, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.update_alerting_config_for_datasource",
            return_value="OK",
        ) as update_config:
            result, error = sync_manager.connect_contact_point(datasource_uid, contact_point_name, create_new)
            if create_new:
                updated_config = update_config.call_args.args[-1]
                assert (result, error) == (True, "")

                contact_point = updated_config["alertmanager_config"]["receivers"][-1]
                assert contact_point["name"] == RECEIVER_NAME_NOT_IN_CONFIG
                if datasource_uid == "grafana":
                    assert (
                        contact_point["grafana_managed_receiver_configs"][-1]["settings"]["url"] == TEST_INTEGRATION_URL
                    )
                    assert contact_point["grafana_managed_receiver_configs"][-1]["type"] == "oncall"
                else:
                    assert contact_point["oncall_configs"][-1]["url"] == TEST_INTEGRATION_URL
            else:
                assert (result, error) == (False, "Contact point was not found")
                assert not update_config.called


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.check_if_oncall_type_is_available",
    return_value=True,
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid,contact_point_name",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED),
    ],
)
@pytest.mark.django_db
def test_disconnect_contact_point_existing_connected(
    mocked_integration_url,
    mocked_contact_point_type_check,
    alertmanager_config,
    datasource_uid,
    contact_point_name,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(alertmanager_config, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.update_alerting_config_for_datasource",
            return_value="OK",
        ) as update_config:
            result, error = sync_manager.disconnect_contact_point(datasource_uid, contact_point_name)
            updated_config = update_config.call_args.args[-1]
            assert (result, error) == (True, "")

            contact_point = updated_config["alertmanager_config"]["receivers"][-2]
            assert contact_point["name"] == ALERTMANAGER_ACTIVE_RECEIVER_CONNECTED

            if datasource_uid == "grafana":
                assert not contact_point.get("grafana_managed_receiver_configs")
            else:
                assert not contact_point.get("webhook_configs")
                assert not contact_point.get("oncall_configs")


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.check_if_oncall_type_is_available",
    return_value=True,
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid,contact_point_name",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", ALERTMANAGER_ACTIVE_RECEIVER_1),
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", RECEIVER_NAME_NOT_IN_CONFIG),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", ALERTMANAGER_ACTIVE_RECEIVER_1),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", RECEIVER_NAME_NOT_IN_CONFIG),
    ],
)
@pytest.mark.django_db
def test_disconnect_contact_point_not_connected(
    mocked_integration_url,
    mocked_contact_point_type_check,
    alertmanager_config,
    datasource_uid,
    contact_point_name,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager

    with patch(
        "apps.grafana_plugin.helpers.GrafanaAPIClient.get_alerting_config",
        return_value=(alertmanager_config, {}),
    ):
        with patch(
            "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.update_alerting_config_for_datasource",
            return_value="OK",
        ) as update_config:
            result, error = sync_manager.disconnect_contact_point(datasource_uid, contact_point_name)
            assert not update_config.called
            if contact_point_name == ALERTMANAGER_ACTIVE_RECEIVER_1:
                assert (result, error) == (False, "OnCall connection was not found in selected contact point")
            else:
                assert (result, error) == (False, "Contact point was not found")


@patch(
    "apps.alerts.models.AlertReceiveChannel.integration_url",
    new_callable=PropertyMock(return_value=TEST_INTEGRATION_URL),
)
@pytest.mark.parametrize(
    "alertmanager_config,datasource_uid,is_grafana_datasource",
    [
        (GRAFANA_ALERTMANAGER_CONFIG, "grafana", True),
        (MIMIR_ALERTMANAGER_CONFIG, "some_uid", False),
    ],
)
@pytest.mark.django_db
def test_remove_integration_config_from_each_contact_point(
    mocked_integration_url,
    alertmanager_config,
    datasource_uid,
    is_grafana_datasource,
    make_organization,
    make_alert_receive_channel,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    )
    sync_manager = alert_receive_channel.grafana_alerting_sync_manager
    updated_config = copy.deepcopy(alertmanager_config)

    sync_manager._remove_integration_config_from_each_contact_point(
        is_grafana_datasource, updated_config.get("alertmanager_config")
    )
    if is_grafana_datasource:
        for receiver in updated_config["alertmanager_config"]["receivers"]:
            for receiver_config in receiver.get("grafana_managed_receiver_configs", []):
                assert receiver_config.get("settings", {}).get("url") != TEST_INTEGRATION_URL
    else:
        for receiver in updated_config["alertmanager_config"]["receivers"]:
            for receiver_config in receiver.get("webhook_configs", []):
                assert receiver_config.get("url") != TEST_INTEGRATION_URL
            for receiver_config in receiver.get("oncall_configs", []):
                assert receiver_config.get("url") != TEST_INTEGRATION_URL
