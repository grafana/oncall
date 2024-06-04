from unittest.mock import patch

import pytest

from apps.alerts.incident_appearance.templaters.alert_templater import TemplatedAlert
from apps.mobile_app.alert_rendering import get_push_notification_subtitle, get_push_notification_title
from apps.mobile_app.backend import MobileAppBackend

MAX_ALERT_TITLE_LENGTH = 200

# this is a dirty hack to get around EXTRA_MESSAGING_BACKENDS being set in settings/ci_test.py
# we can't simply change the value because 100s of tests fail as they rely on the value being set to a specific value 🫠
# see where this value is used in the unitest.mock.patch calls down below for more context
backend = MobileAppBackend(notification_channel_id=5)


def _make_messaging_backend_template(title_template=None, message_template=None) -> str:
    return {"MOBILE_APP": {"title": title_template, "message": message_template}}


@pytest.mark.parametrize(
    "critical,expected_title",
    [
        (True, "New Important Alert"),
        (False, "New Alert"),
    ],
)
@pytest.mark.django_db
def test_get_push_notification_title_no_template_set(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    critical,
    expected_title,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    assert get_push_notification_title(alert_group, critical) == expected_title


@pytest.mark.parametrize(
    "template,payload,expected_title",
    [
        ("{{ payload.foo }}", {"foo": "bar"}, "bar"),
        # template resolves to falsy value, make sure we don't show an empty notification title
        ("{{ payload.foo }}", {}, "New Alert"),
        ("oh nooo", {}, "oh nooo"),
    ],
)
@patch("apps.base.messaging._messaging_backends", return_value={"MOBILE_APP": backend})
@pytest.mark.django_db
def test_get_push_notification_title_template_set(
    _mock_messaging_backends,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    template,
    payload,
    expected_title,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        messaging_backends_templates=_make_messaging_backend_template(title_template=template),
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    assert get_push_notification_title(alert_group, False) == expected_title


@pytest.mark.parametrize(
    "alert_title",
    [
        "Some short title",
        "Some long title" * 100,
    ],
)
@patch("apps.mobile_app.alert_rendering.AlertMobileAppTemplater.render")
@pytest.mark.django_db
def test_get_push_notification_subtitle_no_template_set(
    mock_alert_templater_render,
    alert_title,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    templated_alert = TemplatedAlert()
    templated_alert.title = alert_title
    mock_alert_templater_render.return_value = templated_alert

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization, messaging_backends_templates=_make_messaging_backend_template()
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, title=alert_title, raw_request_data={"title": alert_title})

    result = get_push_notification_subtitle(alert_group)

    expected_alert_title = (
        f"{alert_title[:MAX_ALERT_TITLE_LENGTH]}..." if len(alert_title) > MAX_ALERT_TITLE_LENGTH else alert_title
    )
    assert len(expected_alert_title) <= MAX_ALERT_TITLE_LENGTH + 3
    assert result == (
        f"#1 {expected_alert_title}\n" + f"via {alert_group.channel.short_name}" + "\nStatus: Firing, alerts: 1"
    )


@pytest.mark.parametrize(
    "template,payload,expected_subtitle",
    [
        ("{{ payload.foo }}", {"foo": "bar"}, "bar"),
        ("oh nooo", {}, "oh nooo"),
    ],
)
@patch("apps.base.messaging._messaging_backends", return_value={"MOBILE_APP": backend})
@pytest.mark.django_db
def test_get_push_notification_subtitle_template_set(
    _mock_messaging_backends,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    template,
    payload,
    expected_subtitle,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        messaging_backends_templates=_make_messaging_backend_template(message_template=template),
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    assert get_push_notification_subtitle(alert_group) == expected_subtitle


@patch("apps.mobile_app.alert_rendering.AlertMobileAppTemplater.render")
@pytest.mark.django_db
def test_get_push_notification_subtitle_template_set_resolves_to_blank_value_doesnt_show_blank_subtitle(
    mock_alert_templater_render,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    alert_title = "Some short title"
    template = "{{ payload.foo }}"
    templated_alert = TemplatedAlert()
    templated_alert.title = alert_title

    mock_alert_templater_render.return_value = templated_alert

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization=organization,
        messaging_backends_templates=_make_messaging_backend_template(message_template=template),
    )
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={"bar": "hello"})

    assert get_push_notification_subtitle(alert_group) == (
        f"#1 {alert_title}\n" + f"via {alert_group.channel.short_name}" + "\nStatus: Firing, alerts: 1"
    )
