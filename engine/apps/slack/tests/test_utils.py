from unittest.mock import Mock, patch

import pytest

from apps.slack.client import SlackClient
from apps.slack.errors import (
    SlackAPIChannelArchivedError,
    SlackAPIChannelNotFoundError,
    SlackAPIError,
    SlackAPIInvalidAuthError,
    SlackAPITokenError,
)
from apps.slack.utils import post_message_to_channel


@pytest.mark.parametrize(
    "error,raise_exception",
    [
        (SlackAPITokenError, False),
        (SlackAPIChannelNotFoundError, False),
        (SlackAPIChannelArchivedError, False),
        (SlackAPIInvalidAuthError, False),
        (SlackAPIError, True),
    ],
)
def test_post_message_to_channel(error, raise_exception):
    organization = Mock()
    with patch.object(SlackClient, "chat_postMessage", side_effect=error(Mock())) as mock_chat_postMessage:
        if raise_exception:
            with pytest.raises(SlackAPIError):
                post_message_to_channel(organization, "test", "test")
        else:
            post_message_to_channel(organization, "test", "test")
        mock_chat_postMessage.assert_called_once()
