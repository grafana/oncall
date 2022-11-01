from typing import List

import pytest
from telegram import InlineKeyboardButton

from apps.alerts.models import AlertReceiveChannel
from apps.telegram.renderers.keyboard import TelegramKeyboardRenderer


def are_buttons_equal(button: InlineKeyboardButton, other: InlineKeyboardButton) -> bool:
    return button.text == other.text and button.callback_data == other.callback_data and button.url == other.url


def are_keyboards_equal(keyboard: List[List[InlineKeyboardButton]], other: List[List[InlineKeyboardButton]]) -> bool:
    if len(keyboard) != len(other):
        return False

    for i in range(len(keyboard)):
        row = keyboard[i]
        other_row = other[i]

        if len(row) != len(other_row):
            return False

        for j in range(len(row)):
            button = row[j]
            other_button = other_row[j]

            if not are_buttons_equal(button, other_button):
                return False

    return True


@pytest.mark.django_db
def test_actions_keyboard_alerting(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    renderer = TelegramKeyboardRenderer(alert_group=alert_group)
    keyboard = renderer.render_actions_keyboard()

    expected_keyboard = [
        [
            InlineKeyboardButton(
                text="Acknowledge",
                callback_data=f"{alert_group.pk}:acknowledge:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Resolve",
                callback_data=f"{alert_group.pk}:resolve:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🔕 forever",
                callback_data=f"{alert_group.pk}:silence:x-oncall-org-id{organization.public_primary_key}",
            ),
            InlineKeyboardButton(
                text="... for 1h",
                callback_data=f"{alert_group.pk}:silence:3600:x-oncall-org-id{organization.public_primary_key}",
            ),
            InlineKeyboardButton(
                text="... for 4h",
                callback_data=f"{alert_group.pk}:silence:14400:x-oncall-org-id{organization.public_primary_key}",
            ),
        ],
    ]

    assert are_keyboards_equal(keyboard.inline_keyboard, expected_keyboard) is True


@pytest.mark.django_db
def test_actions_keyboard_acknowledged(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    alert_group.acknowledge_by_user(user)

    renderer = TelegramKeyboardRenderer(alert_group=alert_group)
    keyboard = renderer.render_actions_keyboard()

    expected_keyboard = [
        [
            InlineKeyboardButton(
                text="Unacknowledge",
                callback_data=f"{alert_group.pk}:unacknowledge:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Resolve",
                callback_data=f"{alert_group.pk}:resolve:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
    ]

    assert are_keyboards_equal(keyboard.inline_keyboard, expected_keyboard) is True


@pytest.mark.django_db
def test_actions_keyboard_resolved(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    alert_group.resolve_by_user(user)

    renderer = TelegramKeyboardRenderer(alert_group=alert_group)
    keyboard = renderer.render_actions_keyboard()

    expected_keyboard = [
        [
            InlineKeyboardButton(
                text="Unresolve",
                callback_data=f"{alert_group.pk}:unresolve:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
    ]

    assert are_keyboards_equal(keyboard.inline_keyboard, expected_keyboard) is True


@pytest.mark.django_db
def test_actions_keyboard_silenced(
    make_organization_and_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA, verbal_name="Test integration"
    )

    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    alert_group.silence_by_user(user, silence_delay=None)

    renderer = TelegramKeyboardRenderer(alert_group=alert_group)
    keyboard = renderer.render_actions_keyboard()

    expected_keyboard = [
        [
            InlineKeyboardButton(
                text="Acknowledge",
                callback_data=f"{alert_group.pk}:acknowledge:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Resolve",
                callback_data=f"{alert_group.pk}:resolve:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Unsilence",
                callback_data=f"{alert_group.pk}:unsilence:x-oncall-org-id{organization.public_primary_key}",
            )
        ],
    ]

    assert are_keyboards_equal(keyboard.inline_keyboard, expected_keyboard) is True


@pytest.mark.django_db
def test_link_to_channel_keyboard():
    keyboard = TelegramKeyboardRenderer.render_link_to_channel_keyboard(link="http://test.com")
    expected_keyboard = [[InlineKeyboardButton(text="Go to the incident", url="http://test.com")]]

    assert are_keyboards_equal(keyboard.inline_keyboard, expected_keyboard) is True
