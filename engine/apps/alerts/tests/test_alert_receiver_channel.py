import os
from unittest import mock
from unittest.mock import patch

import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse

from apps.alerts.models import AlertReceiveChannel
from common.api_helpers.utils import create_engine_url
from common.exceptions import UnableToSendDemoAlert
from settings.base import DatabaseTypes


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
        f"integrations:{alert_receive_channel.integration}",
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
@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"foo": "bar"},
    ],
)
def test_send_demo_alert(mocked_create_alert, make_organization, make_alert_receive_channel, payload):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_WEBHOOK
    )
    alert_receive_channel.send_demo_alert(payload=payload)
    assert mocked_create_alert.called
    assert mocked_create_alert.call_args.args[1]["is_demo"]
    assert (
        mocked_create_alert.call_args.args[1]["raw_request_data"] == payload
        or alert_receive_channel.config.example_payload
    )


@mock.patch("apps.integrations.tasks.create_alertmanager_alerts.apply_async", return_value=None)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "integration",
    [
        AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        AlertReceiveChannel.INTEGRATION_GRAFANA,
        AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING,
    ],
)
@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"alerts": [{"foo": "bar"}]},
    ],
)
def test_send_demo_alert_alertmanager_payload_shape(
    mocked_create_alert, make_organization, make_alert_receive_channel, integration, payload
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)
    alert_receive_channel.send_demo_alert(payload=payload)
    assert mocked_create_alert.called
    assert mocked_create_alert.call_args.args[1]["is_demo"]
    assert (
        mocked_create_alert.call_args.args[1]["alert"] == payload["alerts"][0]
        if payload
        else alert_receive_channel.config.example_payload["alerts"][0]
    )


@mock.patch("apps.integrations.tasks.create_alert.apply_async", return_value=None)
@pytest.mark.parametrize(
    "integration", [config.slug for config in AlertReceiveChannel._config if not config.is_demo_alert_enabled]
)
@pytest.mark.django_db
def test_send_demo_alert_not_enabled(mocked_create_alert, make_organization, make_alert_receive_channel, integration):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)

    with pytest.raises(UnableToSendDemoAlert):
        alert_receive_channel.send_demo_alert()

    assert not mocked_create_alert.called


@pytest.mark.django_db
def test_notify_maintenance_no_general_channel(make_organization, make_alert_receive_channel):
    organization = make_organization(default_slack_channel=None)
    alert_receive_channel = make_alert_receive_channel(organization)

    with patch("apps.alerts.models.alert_receive_channel.post_message_to_channel") as mock_post_message:
        alert_receive_channel.notify_about_maintenance_action("maintenance mode enabled")

    assert mock_post_message.call_count == 0


@pytest.mark.django_db
def test_notify_maintenance_with_general_channel(
    make_organization,
    make_alert_receive_channel,
    make_slack_team_identity,
    make_slack_channel,
):
    slack_channel = make_slack_channel(make_slack_team_identity())
    organization = make_organization(default_slack_channel=slack_channel)
    alert_receive_channel = make_alert_receive_channel(organization)

    with patch("apps.alerts.models.alert_receive_channel.post_message_to_channel") as mock_post_message:
        alert_receive_channel.notify_about_maintenance_action("maintenance mode enabled")

    mock_post_message.assert_called_once_with(
        organization, organization.default_slack_channel.slack_id, "maintenance mode enabled"
    )


@pytest.mark.django_db
def test_get_or_create_manual_integration_deleted_team(
    make_organization,
    make_team,
    make_slack_team_identity,
    make_slack_channel,
):
    slack_channel = make_slack_channel(make_slack_team_identity())
    organization = make_organization(default_slack_channel=slack_channel)

    # setup general manual integration
    general_manual = AlertReceiveChannel.get_or_create_manual_integration(
        organization=organization, team=None, integration=AlertReceiveChannel.INTEGRATION_MANUAL, defaults={}
    )
    # setup another team manual integration
    team1 = make_team(organization)
    team1_manual = AlertReceiveChannel.get_or_create_manual_integration(
        organization=organization, team=team1, integration=AlertReceiveChannel.INTEGRATION_MANUAL, defaults={}
    )

    # team is deleted
    team1.delete()
    team1_manual.refresh_from_db()
    assert team1_manual.team is None

    # it should still be possible to get a manual integration for general team
    integration = AlertReceiveChannel.get_or_create_manual_integration(
        organization=organization, team=None, integration=AlertReceiveChannel.INTEGRATION_MANUAL, defaults={}
    )
    assert integration == general_manual


@pytest.mark.django_db
@pytest.mark.parametrize(
    "integration",
    [
        AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
    ],
)
def test_alertmanager_available_for_heartbeat(make_organization, make_alert_receive_channel, integration):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)
    assert alert_receive_channel.is_available_for_integration_heartbeat


@pytest.mark.django_db
def test_delete_duplicate_names(make_organization, make_alert_receive_channel):
    """Check that it's possible to delete two integrations with the same name at once."""
    organization = make_organization()
    for _ in range(2):
        make_alert_receive_channel(organization, verbal_name="duplicate")
    organization.alert_receive_channels.all().delete()


@patch("apps.alerts.models.alert_receive_channel.metrics_add_integrations_to_cache")
@pytest.mark.django_db
def test_create_missing_direct_paging_integrations(
    mock_metrics_add_integrations_to_cache,
    make_organization,
    make_team,
    make_alert_receive_channel,
    make_channel_filter,
):
    organization = make_organization()

    # two teams with no direct paging integration
    team1 = make_team(organization)
    team2 = make_team(organization)

    # team with direct paging integration
    team3 = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(
        organization, team=team3, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
    )
    make_channel_filter(alert_receive_channel, is_default=True, order=0)

    # create missing direct paging integration for organization
    AlertReceiveChannel.objects.create_missing_direct_paging_integrations(organization)

    assert organization.alert_receive_channels.count() == 3

    # check that missing integrations and default routes were created
    #
    # NOTE: we explicitly don't test team3, it already has a Direct Paging integraiton associated with it
    # and AlertReceiveChannel.objects.create_missing_direct_paging_integrations is not responsible for filling
    # in missing routes.
    #
    # See apps/alerts/migrations/0072_upsert_direct_paging_integration_routes.py which is a data migration that does
    # exactly this.
    for team in [team1, team2]:
        alert_receive_channel = organization.alert_receive_channels.get(team=team)

        direct_paging_integration_routes = alert_receive_channel.channel_filters.all()

        assert direct_paging_integration_routes.count() == 2

        for route in direct_paging_integration_routes:
            if route.is_default:
                assert route.order == 1
                assert route.filtering_term is None
            else:
                assert route.order == 0
                assert route.filtering_term == "{{ payload.oncall.important }}"
                assert route.filtering_term_type == route.FILTERING_TERM_TYPE_JINJA2

    mock_metrics_add_integrations_to_cache.assert_called_once()


@pytest.mark.django_db
def test_create_duplicate_direct_paging_integrations(make_organization, make_team, make_alert_receive_channel):
    """Check that it's not possible to have more than one active direct paging integration per team."""

    # MariaDB is not supported for this test
    # See comment: https://github.com/grafana/oncall/commit/381a9ecf54bf0dd076f233b207c13d72ed792181#diff-9d96504027309f2bd1e95352bac1433b09b60eb4fafb611b52a6c15ed16cbc48R219-R223
    is_local_dev_env = os.environ.get("DJANGO_SETTINGS_MODULE") == "settings.dev"
    is_db_type_mysql = settings.DATABASE_TYPE == DatabaseTypes.MYSQL
    if is_local_dev_env and is_db_type_mysql:
        pytest.skip("This test is not supported by Mariadb (used by settings.dev)")

    organization = make_organization()
    team = make_team(organization)
    make_alert_receive_channel(organization, team=team, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)

    with pytest.raises(IntegrityError):
        arc = AlertReceiveChannel(
            organization=organization,
            team=team,
            integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
        )
        super(AlertReceiveChannel, arc).save()  # bypass the custom save method, so that IntegrityError is raised
