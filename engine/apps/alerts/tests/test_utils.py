import socket
from unittest.mock import patch

import pytest

from apps.alerts.utils import request_outgoing_webhook


@pytest.mark.django_db
def test_request_outgoing_webhook_cannot_resolve_name():
    with patch("apps.alerts.utils.socket.gethostbyname", side_effect=socket.gaierror):
        success, err = request_outgoing_webhook("http://something.something/webhook", "GET")
    assert success is False
    assert err == "Cannot resolve name in url"
