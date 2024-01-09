from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

TELEGRAM_USER_ID = 777000
TELEGRAM_USER_NAME = "Telegram"
TELEGRAM_USER = {"from_user_id": TELEGRAM_USER_ID, "from_user_name": TELEGRAM_USER_NAME}

NON_TELEGRAM_USER_ID = 123456789
NON_TELEGRAM_USER_NAME = "Johnny Appleseed"
NON_TELEGRAM_USER = {"from_user_id": NON_TELEGRAM_USER_ID, "from_user_name": NON_TELEGRAM_USER_NAME}

CHANNEL_NAME = "Testing Testing Testing"
DISCUSSION_GROUP_NAME = "joey oncall testing"


def _base_message(from_user_id, from_user_name):
    return {
        "update_id": 822154680,
        "message": {
            "new_chat_members": [],
            "sender_chat": {
                "type": "channel",
                "title": "Asteroid",
                "id": -1001672798904,
            },
            "text": "foo bar baz",
            "channel_chat_created": False,
            "group_chat_created": False,
            "delete_chat_photo": False,
            "new_chat_photo": [],
            "forward_date": 1704305084,
            "photo": [],
            "caption_entities": [],
            "chat": {
                "type": "supergroup",
                "title": CHANNEL_NAME,
                "id": -1001760329920,
            },
            "is_automatic_forward": True,
            "entities": [],
            "message_id": 173,
            "supergroup_chat_created": False,
            "date": 1704350566,
            "from": {
                "is_bot": False,
                "first_name": from_user_name,
                "id": from_user_id,
            },
        },
    }


@pytest.fixture
def make_channel_message_webhook_payload():
    def _make_channel_message_webhook_payload(from_user_id, from_user_name):
        return _base_message(from_user_id, from_user_name) | {
            "forward_from": {
                "is_bot": False,
                "username": "foobarbaz",
                "first_name": from_user_name,
                "is_premium": True,
                "id": 352445997,
            },
        }

    return _make_channel_message_webhook_payload


@pytest.fixture
def make_discussion_group_message_webhook_payload():
    def _make_discussion_group_message_webhook_payload(from_user_id, from_user_name):
        return _base_message(from_user_id, from_user_name) | {
            "forward_from_message_id": 6,
            "forward_signature": from_user_name,
            "forward_from_chat": {
                "type": "channel",
                "id": -1002035090491,
                "title": DISCUSSION_GROUP_NAME,
            },
        }

    return _make_discussion_group_message_webhook_payload


@pytest.mark.django_db
@patch("apps.telegram.updates.update_handlers.channel_to_group_forward.TelegramClient")
@pytest.mark.parametrize("from_user", [TELEGRAM_USER, NON_TELEGRAM_USER])
def test_we_can_successfully_receive_an_update_for_a_message_within_a_channel(
    _MockTelegramClient,
    make_channel_message_webhook_payload,
    from_user,
):
    url = reverse("telegram:incoming_webhook")
    client = APIClient()
    response = client.post(url, make_channel_message_webhook_payload(**from_user), format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@patch("apps.telegram.updates.update_handlers.channel_to_group_forward.TelegramClient")
@pytest.mark.parametrize("from_user", [TELEGRAM_USER, NON_TELEGRAM_USER])
def test_we_can_successfully_receive_an_update_for_a_message_within_a_channels_discussion_group(
    _MockTelegramClient,
    make_discussion_group_message_webhook_payload,
    from_user,
):
    url = reverse("telegram:incoming_webhook")
    client = APIClient()
    response = client.post(url, make_discussion_group_message_webhook_payload(**from_user), format="json")
    assert response.status_code == status.HTTP_200_OK
