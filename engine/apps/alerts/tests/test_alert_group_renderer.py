import pytest

from apps.alerts.incident_appearance.renderers.sms_renderer import AlertGroupSMSBundleRenderer
from apps.alerts.incident_appearance.templaters import AlertSlackTemplater, AlertWebTemplater
from apps.alerts.models import AlertGroup
from apps.base.models import UserNotificationPolicy
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
def test_render_web_alert_links(
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

    links = [f"http://example.com/{i}" for i in range(10)] + ["http://example2.com"] * 5
    alert = make_alert(alert_group=alert_group, raw_request_data={"message": "\n".join(links)})

    templater = AlertWebTemplater(alert)
    templated_alert = templater.render()
    assert templated_alert.message == "<p>{}</p>".format(
        "<br/>\n".join([f'<a href="{link}">{link}</a> ' for link in links])
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com", "https://example.com"),
        ('https://some-url"<script>hey</script>', None),
        ("https://example.com?something=foo&else=bar", "https://example.com?something=foo&else=bar"),
    ],
)
def test_render_web_image_url(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    url,
    expected,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        web_image_url_template="{{ payload.image_url }}",
    )
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data={"image_url": url})

    templater = AlertWebTemplater(alert)
    templated_alert = templater.render()
    assert templated_alert.image_url == expected


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


@pytest.mark.django_db
def test_alert_group_sms_bundle_renderer(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_notification_bundle,
):
    organization, user = make_organization_and_user()
    alert_receive_channel_1 = make_alert_receive_channel(
        organization,
    )
    alert_receive_channel_2 = make_alert_receive_channel(
        organization,
    )
    alert_group_1 = make_alert_group(alert_receive_channel_1)
    alert_group_2 = make_alert_group(alert_receive_channel_1)
    alert_group_3 = make_alert_group(alert_receive_channel_1)
    alert_group_4 = make_alert_group(alert_receive_channel_2)

    notification_bundle = make_user_notification_bundle(user, UserNotificationPolicy.NotificationChannel.SMS)

    # render 1 alert group and 1 channel
    notification_bundle.append_notification(alert_group_1, None)
    renderer = AlertGroupSMSBundleRenderer(notification_bundle.notifications.all())
    message = renderer.render()
    assert message == (
        f"Grafana OnCall: Alert group #{alert_group_1.inside_organization_number} "
        f"from stack: {organization.stack_slug}, "
        f"integration: {alert_receive_channel_1.short_name}."
    )

    # render 3 alert groups and 1 channel
    notification_bundle.append_notification(alert_group_2, None)
    notification_bundle.append_notification(alert_group_3, None)
    renderer = AlertGroupSMSBundleRenderer(notification_bundle.notifications.all())
    message = renderer.render()
    assert message == (
        f"Grafana OnCall: Alert groups #{alert_group_1.inside_organization_number}, "
        f"#{alert_group_2.inside_organization_number}, #{alert_group_3.inside_organization_number} "
        f"from stack: {organization.stack_slug}, "
        f"integration: {alert_receive_channel_1.short_name}."
    )

    # render 4 alert groups and 2 channels
    notification_bundle.append_notification(alert_group_4, None)
    renderer = AlertGroupSMSBundleRenderer(notification_bundle.notifications.all())
    message = renderer.render()
    assert message == (
        f"Grafana OnCall: Alert groups #{alert_group_1.inside_organization_number}, "
        f"#{alert_group_2.inside_organization_number}, #{alert_group_3.inside_organization_number} and 1 more "
        f"from stack: {organization.stack_slug}, "
        f"integrations: {alert_receive_channel_1.short_name} and 1 more."
    )
