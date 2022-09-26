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


@pytest.mark.django_db
def test_request_outgoing_webhook_resolve_name_without_port():
    with patch("apps.alerts.utils.socket.gethostbyname") as mock_gethostbyname:
        mock_gethostbyname.return_value = "127.0.0.1"
        request_outgoing_webhook("http://something.something:9000/webhook", "GET")
    assert mock_gethostbyname.call_args_list[0].args[0] == "something.something"
