import pytest

from apps.alerts.incident_appearance.templaters import AlertSlackTemplater
from apps.alerts.models import AlertGroup
from config_integrations import grafana


@pytest.mark.django_db
def test_render_alert(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(
        organization,
    )
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data=grafana.tests["payload"])

    templater = AlertSlackTemplater(alert)
    templated_alert = templater.render()
    assert templated_alert.title == grafana.tests["slack"]["title"].format(
        web_link=alert_group.web_link,
        integration_name=alert_receive_channel.verbal_name,
    )
    assert templated_alert.message == grafana.tests["slack"]["message"]
    assert templated_alert.image_url == grafana.tests["slack"]["image_url"]


@pytest.mark.django_db
def test_getattr_template(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    slack_title_template = "Incident"
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization, slack_title_template=slack_title_template)
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data={})

    renderer = AlertSlackTemplater(alert)
    template = renderer.template_manager.get_attr_template("title", alert_receive_channel, render_for="slack")
    assert template == slack_title_template


@pytest.mark.django_db
def test_getattr_template_with_no_template(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(
        organization,
    )
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data={})

    renderer = AlertSlackTemplater(alert)
    template = renderer.template_manager.get_attr_template("title", alert_receive_channel, render_for="slack")
    assert template == grafana.slack_title


@pytest.mark.django_db
def test_getdefault_attr_template_non_existing(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(
        organization,
    )
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data={})

    renderer = AlertSlackTemplater(alert)
    default_template = renderer.template_manager.get_default_attr_template(
        "title", alert_receive_channel, render_for="invalid_render_for"
    )
    assert default_template is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "source,expected_text",
    [
        (AlertGroup.SOURCE, "Acknowledged by alert source"),
        (AlertGroup.USER, "Acknowledged by {username}"),
    ],
)
def test_get_acknowledge_text(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    source,
    expected_text,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    alert_group.acknowledge(acknowledged_by=source, acknowledged_by_user=user)

    assert alert_group.get_acknowledge_text() == expected_text.format(username=user.get_username_with_slack_verbal())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "source,expected_text",
    [
        (AlertGroup.SOURCE, "Resolved by alert source"),
        (AlertGroup.LAST_STEP, "Resolved automatically"),
        (AlertGroup.WIPED, "Resolved by wipe"),
        (AlertGroup.DISABLE_MAINTENANCE, "Resolved by stop maintenance"),
        (AlertGroup.USER, "Resolved by {username}"),
    ],
)
def test_get_resolved_text(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    source,
    expected_text,
):
    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    alert_group.resolve(resolved_by=source, resolved_by_user=user)

    assert alert_group.get_resolve_text() == expected_text.format(username=user.get_username_with_slack_verbal())
