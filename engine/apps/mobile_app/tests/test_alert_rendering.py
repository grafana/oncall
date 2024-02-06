from unittest.mock import patch

import pytest

from apps.alerts.incident_appearance.templaters.alert_templater import TemplatedAlert
from apps.mobile_app.alert_rendering import get_push_notification_subtitle, get_push_notification_title
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning

MAX_ALERT_TITLE_LENGTH = 200


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
    critical,
    expected_title,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert alert_receive_channel.mobile_app_title_template is None
    assert get_push_notification_title(alert_group, critical) == expected_title


@pytest.mark.parametrize(
    "template,payload,labels,expected_title",
    [
        ("{{ payload.foo }}", {"foo": "bar"}, {}, "bar"),
        ("{{ labels.hello }}", {}, {"hello": "world"}, "world"),
        ("{{ payload.foo }} {{ labels.bar }}", {"foo": "hello"}, {"bar": "world"}, "hello world"),
        # template resolves to falsy value, make sure we don't show an empty notification title
        ("{{ payload.foo }}", {"bar": "hello"}, {}, "New Alert"),
        ("oh nooo", {}, {}, "oh nooo"),
        ("payload.foo }}", {}, {}, "payload.foo }}"),
    ],
)
@patch("apps.mobile_app.alert_rendering.gather_labels_from_alert_receive_channel_and_raw_request_data")
@pytest.mark.django_db
def test_get_push_notification_title_template_set(
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    template,
    payload,
    labels,
    expected_title,
):
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value = labels

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization, mobile_app_title_template=template)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    assert alert_receive_channel.mobile_app_title_template == template
    assert get_push_notification_title(alert_group, False) == expected_title


@pytest.mark.parametrize("JinjaExceptionClass", [JinjaTemplateError, JinjaTemplateWarning])
@patch("apps.mobile_app.alert_rendering.apply_jinja_template_to_alert_payload_and_labels")
@patch(
    "apps.mobile_app.alert_rendering.gather_labels_from_alert_receive_channel_and_raw_request_data", return_value=None
)
@pytest.mark.django_db
def test_get_push_notification_title_template_set_jinja_exception(
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    mock_apply_jinja_template_to_alert_payload_and_labels,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    JinjaExceptionClass,
):
    mock_apply_jinja_template_to_alert_payload_and_labels.side_effect = JinjaExceptionClass("foo")

    payload = {"foo": "bar"}
    template = "{{ payload.foo }}"

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization, mobile_app_title_template=template)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    assert alert_receive_channel.mobile_app_title_template == template
    assert get_push_notification_title(alert_group, False) == "New Alert"

    mock_apply_jinja_template_to_alert_payload_and_labels.assert_called_once_with(
        template,
        payload,
        mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value,
        result_length_limit=MAX_ALERT_TITLE_LENGTH,
    )


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
    alert_receive_channel = make_alert_receive_channel(organization=organization)

    assert alert_receive_channel.mobile_app_message_template is None

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
    "template,payload,labels,expected_subtitle",
    [
        ("{{ payload.foo }}", {"foo": "bar"}, {}, "bar"),
        ("{{ labels.hello }}", {}, {"hello": "world"}, "world"),
        ("{{ payload.foo }} {{ labels.bar }}", {"foo": "hello"}, {"bar": "world"}, "hello world"),
        ("oh nooo", {}, {}, "oh nooo"),
        ("payload.foo }}", {}, {}, "payload.foo }}"),
    ],
)
@patch("apps.mobile_app.alert_rendering.gather_labels_from_alert_receive_channel_and_raw_request_data")
@pytest.mark.django_db
def test_get_push_notification_subtitle_template_set(
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    template,
    payload,
    labels,
    expected_subtitle,
):
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value = labels

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization, mobile_app_message_template=template)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    assert alert_receive_channel.mobile_app_message_template == template
    assert get_push_notification_subtitle(alert_group) == expected_subtitle


@patch("apps.mobile_app.alert_rendering.gather_labels_from_alert_receive_channel_and_raw_request_data")
@patch("apps.mobile_app.alert_rendering.AlertMobileAppTemplater.render")
@pytest.mark.django_db
def test_get_push_notification_subtitle_template_set_resolves_to_blank_value_doesnt_show_blank_subtitle(
    mock_alert_templater_render,
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    alert_title = "Some short title"
    template = "{{ payload.foo }}"
    templated_alert = TemplatedAlert()
    templated_alert.title = alert_title

    mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value = {}
    mock_alert_templater_render.return_value = templated_alert

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization, mobile_app_message_template=template)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={"bar": "hello"})

    assert alert_receive_channel.mobile_app_message_template == template
    assert get_push_notification_subtitle(alert_group) == (
        f"#1 {alert_title}\n" + f"via {alert_group.channel.short_name}" + "\nStatus: Firing, alerts: 1"
    )


@pytest.mark.parametrize("JinjaExceptionClass", [JinjaTemplateError, JinjaTemplateWarning])
@patch("apps.mobile_app.alert_rendering.apply_jinja_template_to_alert_payload_and_labels")
@patch(
    "apps.mobile_app.alert_rendering.gather_labels_from_alert_receive_channel_and_raw_request_data", return_value=None
)
@patch("apps.mobile_app.alert_rendering.AlertMobileAppTemplater.render")
@pytest.mark.django_db
def test_get_push_notification_subtitle_template_set_jinja_exception(
    mock_alert_templater_render,
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    mock_apply_jinja_template_to_alert_payload_and_labels,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    JinjaExceptionClass,
):
    alert_title = "Some short title"
    templated_alert = TemplatedAlert()
    templated_alert.title = alert_title
    mock_alert_templater_render.return_value = templated_alert

    mock_apply_jinja_template_to_alert_payload_and_labels.side_effect = JinjaExceptionClass("foo")

    payload = {"foo": "bar"}
    template = "{{ payload.foo }}"

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization=organization, mobile_app_message_template=template)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=payload)

    result = get_push_notification_subtitle(alert_group)

    mock_apply_jinja_template_to_alert_payload_and_labels.assert_called_once_with(
        template,
        payload,
        mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value,
        result_length_limit=MAX_ALERT_TITLE_LENGTH,
    )

    assert alert_receive_channel.mobile_app_message_template == template
    assert result == (f"#1 {alert_title}\n" + f"via {alert_group.channel.short_name}" + "\nStatus: Firing, alerts: 1")
