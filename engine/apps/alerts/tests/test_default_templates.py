import pytest
from jinja2 import TemplateSyntaxError

from apps.alerts.incident_appearance.templaters import (
    AlertEmailTemplater,
    AlertPhoneCallTemplater,
    AlertSlackTemplater,
    AlertSmsTemplater,
    AlertTelegramTemplater,
    AlertWebTemplater,
)
from apps.alerts.models import Alert, AlertReceiveChannel
from common.jinja_templater import jinja_template_env
from common.utils import getattrd
from config_integrations import grafana


@pytest.mark.django_db
@pytest.mark.parametrize(
    "integration, template_module",
    # Test only the integrations that have "tests" field in configuration
    [
        (
            integration.slug,
            integration,
        )
        for integration in AlertReceiveChannel._config
        if hasattr(integration, "tests")
    ],
)
def test_default_templates(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    integration,
    template_module,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)
    alert_group = make_alert_group(alert_receive_channel)

    alert = make_alert(alert_group=alert_group, raw_request_data=template_module.tests.get("payload"))

    slack_templater = AlertSlackTemplater(alert)
    web_templater = AlertWebTemplater(alert)
    sms_templater = AlertSmsTemplater(alert)
    email_templater = AlertEmailTemplater(alert)
    telegram_templater = AlertTelegramTemplater(alert)
    phone_call_templater = AlertPhoneCallTemplater(alert)
    templaters = {
        "slack": slack_templater,
        "web": web_templater,
        "sms": sms_templater,
        "email": email_templater,
        "telegram": telegram_templater,
        "phone_call": phone_call_templater,
    }
    for notification_channel, templater in templaters.items():
        rendered_alert = templater.render()
        for attr in ["title", "message", "image_url"]:
            expected = template_module.tests.get(notification_channel).get(attr)
            if expected is not None:
                expected = expected.format(
                    web_link=alert.group.web_link, integration_name=alert_receive_channel.verbal_name
                )

            rendered_attr = getattr(rendered_alert, attr)
            assert rendered_attr == expected, (
                f"{alert_receive_channel}'s {notification_channel} {attr} " f"is not equal to expected"
            )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "integration, template_module",
    [
        (AlertReceiveChannel.INTEGRATION_GRAFANA, grafana),
    ],
)
def test_render_group_data_templates(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    integration,
    template_module,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    alert_receive_channel = make_alert_receive_channel(organization, integration=integration)

    group_data = Alert.render_group_data(alert_receive_channel, template_module.tests.get("payload"))

    assert group_data.group_distinction == template_module.tests.get("group_distinction")
    assert group_data.is_resolve_signal == template_module.tests.get("is_resolve_signal")
    assert group_data.is_acknowledge_signal == template_module.tests.get("is_acknowledge_signal")


def test_default_templates_are_valid():
    template_names = AlertReceiveChannel.template_names

    for integration in AlertReceiveChannel._config:
        for template_name in template_names:
            template = getattrd(integration, f"{template_name}", None)
            if template is not None:
                try:
                    jinja_template_env.from_string(template)
                except TemplateSyntaxError as e:
                    pytest.fail(e.message)
