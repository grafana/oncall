import pytest


@pytest.mark.django_db
def test_escaping_payload_with_double_quotes(
    make_organization,
    make_custom_action,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_payload = {
        "text": '"Hello world"',
    }

    alert = make_alert(alert_group=alert_group, raw_request_data=alert_payload)

    custom_button = make_custom_action(
        name="github_button",
        webhook="https://github.com/",
        user="Chris Vanstras",
        password="qwerty",
        data='{\n "text" : "{{ alert_payload.text }}"\n}',
        authorization_header="auth_token",
        organization=organization,
    )

    custom_button.build_post_kwargs(alert)


@pytest.mark.django_db
def test_escaping_payload_with_single_quote_in_string(
    make_organization,
    make_custom_action,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    alert_payload = {
        "text": "Hi, it's alert",
    }

    alert = make_alert(alert_group=alert_group, raw_request_data=alert_payload)

    custom_button = make_custom_action(
        name="github_button",
        webhook="https://github.com/",
        user="Chris Vanstras",
        password="qwerty",
        data='{"data" : "{{ alert_payload }}"}',
        authorization_header="auth_token",
        organization=organization,
    )

    custom_button.build_post_kwargs(alert)
