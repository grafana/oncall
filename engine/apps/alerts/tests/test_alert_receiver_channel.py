from unittest import mock
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from common.api_helpers.utils import create_engine_url


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "https://site.com/",
        "https://site.com",
    ],
)
def test_integration_url(make_organization, make_alert_receive_channel, url, settings):
    settings.BASE_URL = url

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    path = reverse(
        f"integrations:{AlertReceiveChannel.INTEGRATIONS_TO_REVERSE_URL_MAP[alert_receive_channel.integration]}",
        kwargs={"alert_channel_key": alert_receive_channel.token},
    )

    assert alert_receive_channel.integration_url == create_engine_url(path)


@pytest.mark.django_db
def test_get_template_attribute_no_backends(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates=None)

    attr = alert_receive_channel.get_template_attribute("TESTONLY", "title")
    assert attr is None


@pytest.mark.django_db
def test_get_template_attribute_backend_not_set(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, messaging_backends_templates={"OTHER": {"title": "the-title"}}
    )

    attr = alert_receive_channel.get_template_attribute("TESTONLY", "title")
    assert attr is None


@pytest.mark.django_db
def test_get_template_attribute_backend_attr_not_set(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, messaging_backends_templates={"TESTONLY": {}})

    attr = alert_receive_channel.get_template_attribute("TESTONLY", "title")
    assert attr is None


@pytest.mark.django_db
def test_get_template_attribute_ok(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, messaging_backends_templates={"TESTONLY": {"title": "the-title"}}
    )

    attr = alert_receive_channel.get_template_attribute("TESTONLY", "title")
    assert attr == "the-title"


@pytest.mark.django_db
def test_get_default_template_attribute_non_existing_backend(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    attr = alert_receive_channel.get_default_template_attribute("INVALID", "title")
    assert attr is None


@pytest.mark.django_db
def test_get_default_template_attribute_fallback_to_web(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    attr = alert_receive_channel.get_default_template_attribute("TESTONLY", "title")
    assert attr == alert_receive_channel.INTEGRATION_TO_DEFAULT_WEB_TITLE_TEMPLATE[alert_receive_channel.integration]


@mock.patch("apps.integrations.tasks.create_alert.apply_async", return_value=None)
@pytest.mark.django_db
def test_send_demo_alert(mocked_create_alert, make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK
    )
    alert_receive_channel.send_demo_alert()
    assert mocked_create_alert.called
    assert mocked_create_alert.call_args.args[1]["is_demo"]
    assert mocked_create_alert.call_args.args[1]["force_route_id"] is None


@mock.patch("apps.integrations.tasks.create_alertmanager_alerts.apply_async", return_value=None)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "integration",
    [
        AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        AlertReceiveChannel.INTEGRATION_GRAFANA,
        AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
    ],
)
def test_send_demo_alert_alertmanager_payload_shape(
    mocked_create_alert, make_organization, make_alert_receive_channel, integration
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)
    alert_receive_channel.send_demo_alert()
    assert mocked_create_alert.called
    assert mocked_create_alert.call_args.args[1]["is_demo"]
    assert mocked_create_alert.call_args.args[1]["force_route_id"] is None


@pytest.mark.django_db
def test_notify_maintenance_no_general_channel(make_organization, make_alert_receive_channel):
    organization = make_organization(general_log_channel_id=None)
    alert_receive_channel = make_alert_receive_channel(organization)

    with patch("apps.alerts.models.alert_receive_channel.post_message_to_channel") as mock_post_message:
        alert_receive_channel.notify_about_maintenance_action("maintenance mode enabled")

    assert mock_post_message.call_count == 0


@pytest.mark.django_db
def test_notify_maintenance_with_general_channel(make_organization, make_alert_receive_channel):
    organization = make_organization(general_log_channel_id="CHANNEL-ID")
    alert_receive_channel = make_alert_receive_channel(organization)

    with patch("apps.alerts.models.alert_receive_channel.post_message_to_channel") as mock_post_message:
        alert_receive_channel.notify_about_maintenance_action("maintenance mode enabled")

    mock_post_message.assert_called_once_with(
        organization, organization.general_log_channel_id, "maintenance mode enabled"
    )


@pytest.mark.django_db
def test_count_alerts_last_week_and_total(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)

    today = timezone.now() + timezone.timedelta(minutes=1)
    alerts_total = 10
    alerts_last_week = 7
    alerts_to_update = []
    for i in range(alerts_total):
        alert = make_alert(alert_group=alert_group, raw_request_data={})
        alert.created_at = today - timezone.timedelta(days=alerts_total - i)
        alerts_to_update.append(alert)

    alert_group.alerts.bulk_update(alerts_to_update, ["created_at"])
    alerts_count_last_week, alert_count_total = alert_receive_channel.alerts_count_last_week_and_total

    assert alerts_count_last_week == alerts_last_week
    assert alert_count_total == alerts_total
