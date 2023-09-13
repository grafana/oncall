import json
from contextlib import suppress
from unittest.mock import patch

import pytest
from django.utils import timezone
from slack_sdk.web import SlackResponse

from apps.slack.client import SlackClient, server_error_retry_handler
from apps.slack.errors import (
    SlackAPICannotDMBotError,
    SlackAPIChannelArchivedError,
    SlackAPIChannelInactiveError,
    SlackAPIChannelNotFoundError,
    SlackAPIError,
    SlackAPIFetchMembersFailedError,
    SlackAPIInvalidAuthError,
    SlackAPIMessageNotFoundError,
    SlackAPIMethodNotSupportedForChannelTypeError,
    SlackAPIPermissionDeniedError,
    SlackAPIPlanUpgradeRequiredError,
    SlackAPIRatelimitError,
    SlackAPIRestrictedActionError,
    SlackAPIServerError,
    SlackAPITokenError,
    SlackAPIUsergroupNotFoundError,
    SlackAPIUserNotFoundError,
    SlackAPIViewNotFoundError,
)


@pytest.mark.django_db
@patch(
    "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
    return_value={"status": 200, "body": '{"ok": true}', "headers": {}},
)
def test_slack_client_ok(mock_request, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)
    client.api_call("auth.test")

    mock_request.assert_called_once()


@pytest.mark.parametrize("status", [500, 503, 504])
@patch.object(
    server_error_retry_handler.interval_calculator,
    "calculate_sleep_duration",
    return_value=0,  # speed up the retries
)
@pytest.mark.django_db
def test_slack_client_unexpected_response(_, monkeypatch, status, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)

    return_value = {"status": status, "body": "non-json", "headers": {}}
    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal", return_value=return_value
    ) as mock_request:
        with pytest.raises(SlackAPIServerError) as exc_info:
            client.api_call("auth.test")
            assert type(exc_info.value.response) is dict

    assert mock_request.call_count == server_error_retry_handler.max_retry_count + 1


@pytest.mark.parametrize("error", ["internal_error", "fatal_error"])
@patch.object(
    server_error_retry_handler.interval_calculator,
    "calculate_sleep_duration",
    return_value=0,  # speed up the retries
)
@pytest.mark.django_db
def test_slack_client_slack_server_error(_, monkeypatch, error, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)

    return_value = {"status": 200, "body": json.dumps({"ok": False, "error": error}), "headers": {}}
    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal", return_value=return_value
    ) as mock_request:
        with pytest.raises(SlackAPIServerError) as exc_info:
            client.api_call("auth.test")
            assert type(exc_info.value.response) is dict

    assert mock_request.call_count == server_error_retry_handler.max_retry_count + 1


@pytest.mark.django_db
@patch(
    "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
    return_value={"status": 200, "body": '{"ok": false, "error": "random_error_123"}', "headers": {}},
)
def test_slack_client_generic_error(mock_request, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)

    with pytest.raises(SlackAPIError) as exc_info:
        client.api_call("auth.test")
        assert type(exc_info.value) is SlackAPIError
        assert type(exc_info.value.response) is SlackResponse

    mock_request.assert_called_once()


@pytest.mark.parametrize(
    "error,error_class",
    [
        ("account_inactive", SlackAPITokenError),
        ("cannot_dm_bot", SlackAPICannotDMBotError),
        ("channel_not_found", SlackAPIChannelNotFoundError),
        ("fatal_error", SlackAPIServerError),
        ("fetch_members_failed", SlackAPIFetchMembersFailedError),
        ("internal_error", SlackAPIServerError),
        ("invalid_auth", SlackAPIInvalidAuthError),
        ("is_archived", SlackAPIChannelArchivedError),
        ("is_inactive", SlackAPIChannelInactiveError),
        ("message_limit_exceeded", SlackAPIRatelimitError),
        ("message_not_found", SlackAPIMessageNotFoundError),
        ("method_not_supported_for_channel_type", SlackAPIMethodNotSupportedForChannelTypeError),
        ("no_such_subteam", SlackAPIUsergroupNotFoundError),
        ("not_found", SlackAPIViewNotFoundError),
        ("permission_denied", SlackAPIPermissionDeniedError),
        ("plan_upgrade_required", SlackAPIPlanUpgradeRequiredError),
        ("rate_limited", SlackAPIRatelimitError),
        ("ratelimited", SlackAPIRatelimitError),
        ("restricted_action", SlackAPIRestrictedActionError),
        ("token_revoked", SlackAPITokenError),
        ("user_not_found", SlackAPIUserNotFoundError),
    ],
)
@patch.object(
    server_error_retry_handler.interval_calculator,
    "calculate_sleep_duration",
    return_value=0,  # speed up the retries if any
)
@pytest.mark.django_db
def test_slack_client_specific_error(_, error, error_class, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)

    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
        return_value={"status": 200, "body": json.dumps({"ok": False, "error": error}), "headers": {}},
    ):
        with pytest.raises(SlackAPIError) as exc_info:
            client.api_call("auth.test")
            assert type(exc_info.value) is error_class
            assert type(exc_info.value.response) is SlackResponse


@pytest.mark.parametrize("error", ["ratelimited", "rate_limited", "message_limit_exceeded"])
@pytest.mark.django_db
def test_slack_client_ratelimit(monkeypatch, error, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)

    return_value = {"status": 429, "body": json.dumps({"ok": False, "error": error}), "headers": {"Retry-After": "42"}}
    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal", return_value=return_value
    ) as mock_request:
        with pytest.raises(SlackAPIRatelimitError) as exc_info:
            client.api_call("auth.test")

    mock_request.assert_called_once()
    assert exc_info.value.retry_after == 42


@pytest.mark.parametrize("error", ["account_inactive", "token_revoked"])
@pytest.mark.django_db
def test_slack_client_mark_token_revoked(error, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    _, slack_team_identity = make_organization_with_slack_team_identity()
    client = SlackClient(slack_team_identity)
    assert slack_team_identity.detected_token_revoked is None

    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
        return_value={"status": 200, "body": json.dumps({"ok": False, "error": error}), "headers": {}},
    ) as mock_request:
        with pytest.raises(SlackAPITokenError):
            client.api_call("auth.test")

    mock_request.assert_called_once()
    slack_team_identity.refresh_from_db()
    assert slack_team_identity.detected_token_revoked is not None


@pytest.mark.parametrize("error", ["account_inactive", "token_revoked"])
@pytest.mark.django_db
def test_slack_client_cant_unmark_token_revoked(error, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    now = timezone.now()
    _, slack_team_identity = make_organization_with_slack_team_identity(detected_token_revoked=now)
    client = SlackClient(slack_team_identity)
    assert slack_team_identity.detected_token_revoked == now

    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
        return_value={"status": 200, "body": json.dumps({"ok": False, "error": error}), "headers": {}},
    ) as mock_request:
        with pytest.raises(SlackAPITokenError):
            client.api_call("auth.test")

    mock_request.assert_called_once()
    slack_team_identity.refresh_from_db()
    assert slack_team_identity.detected_token_revoked == now


@pytest.mark.parametrize("body", [{"ok": False, "error": "ratelimited"}, {"ok": True}])
@pytest.mark.django_db
def test_slack_client_unmark_token_revoked(body, monkeypatch, make_organization_with_slack_team_identity):
    monkeypatch.undo()  # undo engine.conftest.mock_slack_api_call

    now = timezone.now()
    _, slack_team_identity = make_organization_with_slack_team_identity(detected_token_revoked=now)
    client = SlackClient(slack_team_identity)
    assert slack_team_identity.detected_token_revoked == now

    with patch(
        "slack_sdk.web.base_client.BaseClient._perform_urllib_http_request_internal",
        return_value={"status": 200, "body": json.dumps(body), "headers": {}},
    ) as mock_request:
        with suppress(SlackAPIError):
            client.api_call("auth.test")

    mock_request.assert_called_once()
    slack_team_identity.refresh_from_db()
    assert slack_team_identity.detected_token_revoked is None
