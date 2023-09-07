import json
from unittest.mock import patch

import pytest

from apps.slack.client import SlackAPIRateLimitException, SlackClientWithErrorHandling


@pytest.mark.parametrize("error", ["ratelimited", "rate_limited", "message_limit_exceeded"])
def test_slack_client_ratelimit(monkeypatch, error):
    # undo engine.conftest.mock_slack_api_call
    monkeypatch.undo()

    return_value = {"status": 429, "body": json.dumps({"ok": False, "error": error}), "headers": {"Retry-After": "42"}}

    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal", return_value=return_value
    ) as mock_request:
        with pytest.raises(SlackAPIRateLimitException) as exc_info:
            SlackClientWithErrorHandling().api_call("auth.test")

    mock_request.assert_called_once()
    assert exc_info.value.retry_after == 42
