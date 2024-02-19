from unittest import mock
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from common.api_helpers.utils import create_engine_url
from common.exceptions import UnableToSendDemoAlert
from engine.management.commands import alertmanager_v2_migrate


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
def test_get_or_create_manual_integration_deleted_team(make_organization, make_team, make_alert_receive_channel):
    organization = make_organization(general_log_channel_id="CHANNEL-ID")
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

    # team with no direct paging integration
    team1 = make_team(organization)

    # team with direct paging integration
    team2 = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(
        organization, team=team2, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
    )
    make_channel_filter(alert_receive_channel, is_default=True, order=0)

    # create missing direct paging integration for organization
    AlertReceiveChannel.objects.create_missing_direct_paging_integrations(organization)

    # check that missing integrations and default routes were created
    assert organization.alert_receive_channels.count() == 2
    mock_metrics_add_integrations_to_cache.assert_called_once()
    for team in [team1, team2]:
        alert_receive_channel = organization.alert_receive_channels.get(
            team=team, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
        )
        assert alert_receive_channel.channel_filters.get().is_default


@pytest.mark.django_db
def test_create_duplicate_direct_paging_integrations(make_organization, make_team, make_alert_receive_channel):
    """Check that it's not possible to have more than one active direct paging integration per team."""

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


@pytest.mark.django_db
def test_alertmanager_v2_migrate_forward(make_organization, make_alert_receive_channel):
    organization = make_organization()

    legacy_alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        slack_title_template="slack_title_template",
        web_title_template="web_title_template",
        grouping_id_template="grouping_id_template",
        resolve_condition_template="resolve_condition_template",
    )

    alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    legacy_grafana_alerting = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    )
    grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    alertmanager_v2_migrate.Command().handle(backward=False)

    legacy_alertmanager.refresh_from_db()
    alertmanager.refresh_from_db()
    legacy_grafana_alerting.refresh_from_db()
    grafana_alerting.refresh_from_db()

    assert legacy_alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert legacy_alertmanager.alertmanager_v2_migrated_at is not None
    assert legacy_alertmanager.slack_title_template is None
    assert legacy_alertmanager.web_title_template is None
    assert legacy_alertmanager.grouping_id_template is None
    assert legacy_alertmanager.resolve_condition_template is None
    assert legacy_alertmanager.alertmanager_v2_backup_templates["slack_title_template"] == "slack_title_template"
    assert legacy_alertmanager.alertmanager_v2_backup_templates["web_title_template"] == "web_title_template"
    assert legacy_alertmanager.alertmanager_v2_backup_templates["grouping_id_template"] == "grouping_id_template"
    assert (
        legacy_alertmanager.alertmanager_v2_backup_templates["resolve_condition_template"]
        == "resolve_condition_template"
    )
    assert legacy_alertmanager.alertmanager_v2_backup_templates["messaging_backends_templates"] is None

    assert legacy_grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert legacy_grafana_alerting.alertmanager_v2_migrated_at is not None
    assert legacy_grafana_alerting.alertmanager_v2_backup_templates is None

    assert alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager.alertmanager_v2_migrated_at is None
    assert alertmanager.slack_title_template == "slack_title_template"
    assert alertmanager.alertmanager_v2_backup_templates is None

    assert grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting.alertmanager_v2_migrated_at is None
    assert grafana_alerting.slack_title_template == "slack_title_template"
    assert grafana_alerting.alertmanager_v2_backup_templates is None


@pytest.mark.django_db
def test_alertmanager_v2_migrate_backward(make_organization, make_alert_receive_channel):
    organization = make_organization()

    migrated_alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        alertmanager_v2_migrated_at=timezone.now(),
        alertmanager_v2_backup_templates={
            "slack_title_template": "slack_title_template",
            "web_title_template": "web_title_template",
            "grouping_id_template": "grouping_id_template",
            "resolve_condition_template": "resolve_condition_template",
        },
    )

    alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    migrated_grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        alertmanager_v2_migrated_at=timezone.now(),
    )
    grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    alertmanager_v2_migrate.Command().handle(backward=True)

    migrated_alertmanager.refresh_from_db()
    alertmanager.refresh_from_db()
    migrated_grafana_alerting.refresh_from_db()
    grafana_alerting.refresh_from_db()

    assert migrated_alertmanager.integration == AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER
    assert migrated_alertmanager.alertmanager_v2_migrated_at is None
    assert migrated_alertmanager.slack_title_template == "slack_title_template"
    assert migrated_alertmanager.web_title_template == "web_title_template"
    assert migrated_alertmanager.grouping_id_template == "grouping_id_template"
    assert migrated_alertmanager.resolve_condition_template == "resolve_condition_template"
    assert migrated_alertmanager.alertmanager_v2_backup_templates is None

    assert migrated_grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    assert migrated_grafana_alerting.alertmanager_v2_migrated_at is None
    assert migrated_grafana_alerting.slack_title_template is None
    assert migrated_grafana_alerting.web_title_template is None
    assert migrated_grafana_alerting.grouping_id_template is None
    assert migrated_grafana_alerting.resolve_condition_template is None
    assert migrated_grafana_alerting.alertmanager_v2_backup_templates is None

    assert alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager.alertmanager_v2_migrated_at is None
    assert alertmanager.slack_title_template == "slack_title_template"
    assert alertmanager.alertmanager_v2_backup_templates is None

    assert grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting.alertmanager_v2_migrated_at is None
    assert grafana_alerting.slack_title_template == "slack_title_template"
    assert grafana_alerting.alertmanager_v2_backup_templates is None


@pytest.mark.django_db
def test_alertmanager_v2_migrate_forward_one(make_organization, make_alert_receive_channel):
    organization = make_organization()
    # org which is not going to be migrated
    organization_2 = make_organization()

    legacy_alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        slack_title_template="slack_title_template",
        web_title_template="web_title_template",
        grouping_id_template="grouping_id_template",
        resolve_condition_template="resolve_condition_template",
    )
    alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    legacy_grafana_alerting = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    )
    grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    # set up same set integrations for second org
    legacy_alertmanager_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
        slack_title_template="slack_title_template",
        web_title_template="web_title_template",
        grouping_id_template="grouping_id_template",
        resolve_condition_template="resolve_condition_template",
    )
    alertmanager_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    legacy_grafana_alerting_2 = make_alert_receive_channel(
        organization_2, integration=AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    )
    grafana_alerting_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    alertmanager_v2_migrate.Command().handle(backward=False, org_id=organization.id)

    legacy_alertmanager.refresh_from_db()
    alertmanager.refresh_from_db()
    legacy_grafana_alerting.refresh_from_db()
    grafana_alerting.refresh_from_db()

    legacy_alertmanager_2.refresh_from_db()
    alertmanager_2.refresh_from_db()
    legacy_grafana_alerting_2.refresh_from_db()
    grafana_alerting_2.refresh_from_db()

    assert legacy_alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert legacy_alertmanager.alertmanager_v2_migrated_at is not None
    assert legacy_alertmanager.slack_title_template is None
    assert legacy_alertmanager.web_title_template is None
    assert legacy_alertmanager.grouping_id_template is None
    assert legacy_alertmanager.resolve_condition_template is None
    assert legacy_alertmanager.alertmanager_v2_backup_templates["slack_title_template"] == "slack_title_template"
    assert legacy_alertmanager.alertmanager_v2_backup_templates["web_title_template"] == "web_title_template"
    assert legacy_alertmanager.alertmanager_v2_backup_templates["grouping_id_template"] == "grouping_id_template"
    assert (
        legacy_alertmanager.alertmanager_v2_backup_templates["resolve_condition_template"]
        == "resolve_condition_template"
    )
    assert legacy_alertmanager.alertmanager_v2_backup_templates["messaging_backends_templates"] is None

    assert legacy_grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert legacy_grafana_alerting.alertmanager_v2_migrated_at is not None
    assert legacy_grafana_alerting.alertmanager_v2_backup_templates is None

    assert alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager.alertmanager_v2_migrated_at is None
    assert alertmanager.slack_title_template == "slack_title_template"
    assert alertmanager.alertmanager_v2_backup_templates is None

    assert grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting.alertmanager_v2_migrated_at is None
    assert grafana_alerting.slack_title_template == "slack_title_template"
    assert grafana_alerting.alertmanager_v2_backup_templates is None

    # check that second org is NOT affected

    # check that legacy alertmanager not affected
    assert legacy_alertmanager_2.integration == AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER
    assert legacy_alertmanager_2.alertmanager_v2_migrated_at is None
    assert legacy_alertmanager_2.slack_title_template == "slack_title_template"
    assert legacy_alertmanager_2.web_title_template == "web_title_template"
    assert legacy_alertmanager_2.grouping_id_template == "grouping_id_template"
    assert legacy_alertmanager_2.resolve_condition_template == "resolve_condition_template"
    assert legacy_alertmanager_2.alertmanager_v2_backup_templates is None

    # check that legacy grafana_alerting not affected
    assert legacy_grafana_alerting_2.integration == AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    assert legacy_grafana_alerting_2.alertmanager_v2_migrated_at is None
    assert legacy_grafana_alerting_2.alertmanager_v2_backup_templates is None

    # check that alertmanager which shouldn't be affected even by migration not touched
    assert alertmanager_2.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager_2.alertmanager_v2_migrated_at is None
    assert alertmanager_2.slack_title_template == "slack_title_template"
    assert alertmanager_2.alertmanager_v2_backup_templates is None

    # same fpr grafana alerting
    assert grafana_alerting_2.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting_2.alertmanager_v2_migrated_at is None
    assert grafana_alerting_2.slack_title_template == "slack_title_template"
    assert grafana_alerting_2.alertmanager_v2_backup_templates is None


@pytest.mark.django_db
def test_alertmanager_v2_migrate_backward_one(make_organization, make_alert_receive_channel):
    organization = make_organization()

    migrated_alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        alertmanager_v2_migrated_at=timezone.now(),
        alertmanager_v2_backup_templates={
            "slack_title_template": "slack_title_template",
            "web_title_template": "web_title_template",
            "grouping_id_template": "grouping_id_template",
            "resolve_condition_template": "resolve_condition_template",
        },
    )

    alertmanager = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    migrated_grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        alertmanager_v2_migrated_at=timezone.now(),
    )
    grafana_alerting = make_alert_receive_channel(
        organization,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    organization_2 = make_organization()

    migrated_alertmanager_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        alertmanager_v2_migrated_at=timezone.now(),
        alertmanager_v2_backup_templates={
            "slack_title_template": "slack_title_template",
            "web_title_template": "web_title_template",
            "grouping_id_template": "grouping_id_template",
            "resolve_condition_template": "resolve_condition_template",
        },
    )
    alertmanager_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
        slack_title_template="slack_title_template",
    )
    migrated_grafana_alerting_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        alertmanager_v2_migrated_at=timezone.now(),
    )
    grafana_alerting_2 = make_alert_receive_channel(
        organization_2,
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        slack_title_template="slack_title_template",
    )

    alertmanager_v2_migrate.Command().handle(backward=True, org_id=organization.id)

    migrated_alertmanager.refresh_from_db()
    alertmanager.refresh_from_db()
    migrated_grafana_alerting.refresh_from_db()
    grafana_alerting.refresh_from_db()

    assert migrated_alertmanager.integration == AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER
    assert migrated_alertmanager.alertmanager_v2_migrated_at is None
    assert migrated_alertmanager.slack_title_template == "slack_title_template"
    assert migrated_alertmanager.web_title_template == "web_title_template"
    assert migrated_alertmanager.grouping_id_template == "grouping_id_template"
    assert migrated_alertmanager.resolve_condition_template == "resolve_condition_template"
    assert migrated_alertmanager.alertmanager_v2_backup_templates is None

    assert migrated_grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING
    assert migrated_grafana_alerting.alertmanager_v2_migrated_at is None
    assert migrated_grafana_alerting.slack_title_template is None
    assert migrated_grafana_alerting.web_title_template is None
    assert migrated_grafana_alerting.grouping_id_template is None
    assert migrated_grafana_alerting.resolve_condition_template is None
    assert migrated_grafana_alerting.alertmanager_v2_backup_templates is None

    assert alertmanager.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager.alertmanager_v2_migrated_at is None
    assert alertmanager.slack_title_template == "slack_title_template"
    assert alertmanager.alertmanager_v2_backup_templates is None

    assert grafana_alerting.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting.alertmanager_v2_migrated_at is None
    assert grafana_alerting.slack_title_template == "slack_title_template"
    assert grafana_alerting.alertmanager_v2_backup_templates is None

    migrated_alertmanager_2.refresh_from_db()
    alertmanager_2.refresh_from_db()
    migrated_grafana_alerting_2.refresh_from_db()
    grafana_alerting_2.refresh_from_db()

    # check that migrated integrations is second org were not touced by backward migration of other org
    assert migrated_alertmanager_2.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert migrated_alertmanager_2.alertmanager_v2_migrated_at is not None
    assert migrated_alertmanager_2.slack_title_template is None
    assert migrated_alertmanager_2.web_title_template is None
    assert migrated_alertmanager_2.grouping_id_template is None
    assert migrated_alertmanager_2.resolve_condition_template is None
    assert migrated_alertmanager_2.alertmanager_v2_backup_templates is not None

    assert migrated_grafana_alerting_2.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert migrated_grafana_alerting_2.alertmanager_v2_migrated_at is not None
    assert migrated_grafana_alerting_2.slack_title_template is None
    assert migrated_grafana_alerting_2.web_title_template is None
    assert migrated_grafana_alerting_2.grouping_id_template is None
    assert migrated_grafana_alerting_2.resolve_condition_template is None
    assert migrated_grafana_alerting_2.alertmanager_v2_backup_templates is None

    assert alertmanager_2.integration == AlertReceiveChannel.INTEGRATION_ALERTMANAGER
    assert alertmanager_2.alertmanager_v2_migrated_at is None
    assert alertmanager_2.slack_title_template == "slack_title_template"
    assert alertmanager_2.alertmanager_v2_backup_templates is None

    assert grafana_alerting_2.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    assert grafana_alerting_2.alertmanager_v2_migrated_at is None
    assert grafana_alerting_2.slack_title_template == "slack_title_template"
    assert grafana_alerting_2.alertmanager_v2_backup_templates is None
